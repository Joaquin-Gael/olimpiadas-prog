from dns.rdtypes.svcbbase import ParamKey
from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import List
from datetime import date
from django.db import transaction
from ninja.errors import HttpError
from .pagination import PaginationParams, paginate_response, DefaultPagination
from ninja.pagination import paginate

from .models import Packages, ComponentPackages, ProductsMetadata, Category
from .schemas import (
    PackageCreate, PackageUpdate, PackageOut, PackageDetailOut, PackageSearchParams,
    ComponentPackageCreate, ComponentPackageUpdate, ComponentPackageOut,
    PackageCompleteCreate, CategoryCreate, CategoryUpdate, CategoryOut
)

package_router = Router(tags=["Packages"])
category_router = Router(tags=["Categories"])
# ──────────────────────────────────────────────────────────────
# MAIN PACKAGE ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/", response={200: List[PackageOut]})
@paginate(DefaultPagination)
def list_packages(
    request, 
    search: PackageSearchParams = Query(...)
):
    """
    Lists all packages with filters and pagination
    """
    queryset = Packages.objects.active()
    
    # Apply search filters
    if search.name:
        queryset = queryset.filter(name__icontains=search.name)
    
    if search.min_price is not None:
        queryset = queryset.filter(final_price__gte=search.min_price)
    
    if search.max_price is not None:
        queryset = queryset.filter(final_price__lte=search.max_price)
    
    if search.min_rating is not None:
        queryset = queryset.filter(rating_average__gte=search.min_rating)
    
    if search.max_rating is not None:
        queryset = queryset.filter(rating_average__lte=search.max_rating)
    
    if search.is_active is not None:
        queryset = queryset.filter(is_active=search.is_active)
    
    if search.product_type:
        # Filter by product type in components
        queryset = queryset.filter(
            componentpackages__product_metadata__product_type=search.product_type
        ).distinct()
    
    # Order by name
    queryset = queryset.order_by('name')

    serialized_list: List[PackageOut] = []
    for pkg in queryset:
        serialized_list.append(
            PackageOut(
                id=pkg.id,
                name=pkg.name,
                description=pkg.description,
                cover_image=pkg.cover_image or None,

                base_price=float(pkg.base_price) if pkg.base_price is not None else None,
                taxes=float(pkg.taxes)         if pkg.taxes      is not None else None,
                final_price=float(pkg.final_price),

                rating_average=float(pkg.rating_average),
                total_reviews=pkg.total_reviews,

                is_active=pkg.is_active,

                created_at=pkg.created_at,
                updated_at=pkg.updated_at,

                duration_days=pkg.duration_days,

                currency='USD',  # o el campo que necesites traer realmente
            )
        )
    
    return serialized_list


@package_router.get("/{package_id}", response=PackageDetailOut)
def get_package(request, package_id: int):
    """
    Gets a specific package with all its components
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    
    # Get ordered components
    components = package.componentpackages.all().order_by('order')
    
    # Prepare component data for the response
    component_data = []
    for comp in components:
        component_data.append({
            "id": comp.id,
            "product_metadata_id": comp.product_metadata_id,
            "order": comp.order,
            "quantity": comp.quantity,
            "title": comp.title,
            "start_date": comp.start_date,
            "end_date": comp.end_date,
            "product_type": comp.product_metadata.product_type,
            "product_name": str(comp.product_metadata.content)
        })
    
    # Prepare category data
    category_data = None
    if package.category:
        category_data = {
            "id": package.category.id,
            "name": package.category.name,
            "description": package.category.description,
            "icon": package.category.icon,
            "is_active": package.category.is_active,
            "created_at": package.category.created_at,
            "updated_at": package.category.updated_at
        }
    
    return {
        **PackageOut.from_orm(package).dict(),
        "category": category_data,
        "components": component_data
    }


@package_router.post("/", response=PackageDetailOut)
@transaction.atomic
def create_package(request, data: PackageCompleteCreate):
    """
    Creates a new package with its components
    """
    try:
        # Create the package
        package_data = data.dict(exclude={'components'})
        
        # Handle cover_image field if None
        if package_data.get('cover_image') is None:
            package_data['cover_image'] = ""  # Establecer string vacío en lugar de None
        
        package = Packages.objects.create(**package_data)
        
        # Create the components
        for comp_data in data.components:
            ComponentPackages.objects.create(
                package=package,
                **comp_data.dict()
            )
        
        # Return the created package with its components
        return get_package(request, package.id)
        
    except ValidationError as e:
        raise HttpError(422, str(getattr(e, 'message_dict', None) or getattr(e, 'messages', str(e))))
    except Exception as e:
        raise ValidationError(f"Error creating the package: {e}")


@package_router.put("/{package_id}", response=PackageDetailOut)
def update_package(request, package_id: int, data: PackageUpdate):
    """
    Updates an existing package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    
    try:
        # Update package fields
        for field, value in data.dict(exclude_unset=True).items():
            setattr(package, field, value)
        
        package.full_clean()
        package.save()
        
        return get_package(request, package.id)
        
    except ValidationError as e:
        raise HttpError(422, str(getattr(e, 'message_dict', None) or getattr(e, 'messages', str(e))))
    except Exception as e:
        raise ValidationError(f"Error updating the package: {e}")


@package_router.delete("/{package_id}")
def delete_package(request, package_id: int):
    """
    Deletes (soft delete) a package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    try:
        package.is_active = False
        package.deleted_at = timezone.now()
        package.save()
        return {"message": "Package deleted successfully"}
    except Exception as e:
        raise ValidationError(f"Error deleting the package: {e}")


# ──────────────────────────────────────────────────────────────
# PACKAGE COMPONENTS ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/{package_id}/components", response=List[ComponentPackageOut])
def list_package_components(request, package_id: int):
    """
    Lists all components of a specific package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    components = package.componentpackages.all().order_by('order')
    return [ComponentPackageOut.from_orm(comp) for comp in components]


@package_router.post("/{package_id}/components", response=ComponentPackageOut)
def add_package_component(request, package_id: int, data: ComponentPackageCreate):
    """
    Adds a new component to a package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    try:
        product_metadata = get_object_or_404(ProductsMetadata, id=data.product_metadata_id)
        component = ComponentPackages.objects.create(
            package=package,
            **data.dict()
        )
        return ComponentPackageOut.from_orm(component)
    except ValidationError as e:
        raise ValidationError(f"Validation error: {e}")
    except Exception as e:
        raise ValidationError(f"Error adding the component: {e}")


@package_router.put("/{package_id}/components/{component_id}", response=ComponentPackageOut)
def update_package_component(
    request, 
    package_id: int, 
    component_id: int, 
    data: ComponentPackageUpdate
):
    """
    Updates a specific component of a package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    component = get_object_or_404(ComponentPackages, id=component_id, package=package)
    try:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(component, field, value)
        component.full_clean()
        component.save()
        return ComponentPackageOut.from_orm(component)
    except ValidationError as e:
        raise ValidationError(f"Validation error: {e}")
    except Exception as e:
        raise ValidationError(f"Error updating the component: {e}")


@package_router.delete("/{package_id}/components/{component_id}")
def remove_package_component(request, package_id: int, component_id: int):
    """
    Deletes a specific component from a package
    """
    package = get_object_or_404(Packages.objects.active(), id=package_id)
    component = get_object_or_404(ComponentPackages, id=component_id, package=package)
    
    try:
        component.delete()
        return {"message": "Component deleted successfully"}
        
    except Exception as e:
        raise ValidationError(f"Error deleting the component: {e}")


# ──────────────────────────────────────────────────────────────
# SPECIAL SEARCH AND FILTER ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/search/featured", response=List[PackageOut])
def get_featured_packages(request, limit: int = 10):
    """
    Gets featured packages (with best rating)
    """
    packages = Packages.objects.active().filter(
        rating_average__gt=0,
        total_reviews__gt=0
    ).order_by('-rating_average', '-total_reviews')[:limit]
    
    return [PackageOut.from_orm(pkg) for pkg in packages]


@package_router.get("/search/by-price-range", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_price_range(
    request, 
    min_price: float, 
    max_price: float
):
    queryset = Packages.objects.active().filter(
        final_price__gte=min_price,
        final_price__lte=max_price
    ).order_by('final_price')
    return queryset


@package_router.get("/search/by-duration", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_duration(
    request, 
    min_days: int, 
    max_days: int
):
    packages = Packages.objects.active().all()
    filtered_packages = [pkg for pkg in packages if pkg.duration_days and min_days <= pkg.duration_days <= max_days]
    return filtered_packages


# ──────────────────────────────────────────────────────────────
# STATISTICS ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/stats/overview")
def get_packages_stats(request):
    """
    Gets general statistics of packages
    """
    total_packages = Packages.objects.active().count()
    active_packages = Packages.objects.active().filter(is_active=True).count()
    
    # Price statistics
    price_stats = Packages.objects.active().aggregate(
        avg_price=Avg('final_price'),
        min_price=Min('final_price'),
        max_price=Max('final_price')
    )
    
    # Rating statistics
    rating_stats = Packages.objects.active().filter(rating_average__gt=0).aggregate(
        avg_rating=Avg('rating_average'),
        total_reviews=Count('total_reviews')
    )
    
    return {
        "total_packages": total_packages,
        "active_packages": active_packages,
        "price_stats": price_stats,
        "rating_stats": rating_stats
    }

# ──────────────────────────────────────────────────────────────
# CATEGORY ENDPOINTS
# ──────────────────────────────────────────────────────────────

@category_router.get("/", response=List[CategoryOut])
def list_categories(request):
    """
    Lists all active categories
    """
    try:
        categories = Category.objects.get().all().order_by('name')
        return [CategoryOut.from_orm(cat) for cat in categories]
    except Exception as e:
        raise HttpError(500, f"Error listing categories: {e}")


@category_router.get("/{category_id}", response=CategoryOut)
def get_category(request, category_id: int):
    """
    Gets a specific category
    """
    category = get_object_or_404(Category.objects.active(), id=category_id)
    return CategoryOut.from_orm(category)


@category_router.post("/", response=CategoryOut)
def create_category(request, data: CategoryCreate):
    """
    Creates a new category
    """
    try:
        category = Category.objects.create(**data.dict())
        return CategoryOut.from_orm(category)
    except Exception as e:
        raise ValidationError(f"Error creating the category: {e}")


@category_router.put("/{category_id}", response=CategoryOut)
def update_category(request, category_id: int, data: CategoryUpdate):
    """
    Updates an existing category
    """
    category = get_object_or_404(Category.objects.active(), id=category_id)
    
    try:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(category, field, value)
        
        category.full_clean()
        category.save()
        
        return CategoryOut.from_orm(category)
    except Exception as e:
        raise ValidationError(f"Error updating the category: {e}")


@category_router.delete("/{category_id}")
def delete_category(request, category_id: int):
    """
    Elimina (soft delete) una categoría
    """
    category = get_object_or_404(Category.objects.active(), id=category_id)
    
    try:
        category.is_active = False
        category.save()
        
        return {"message": "Categoría eliminada correctamente"}
    except Exception as e:
        raise ValidationError(f"Error al eliminar la categoría: {e}")


@package_router.get("/{category_id}/packages", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_category(request, category_id: int):
    queryset = Packages.objects.active().filter(category_id=category_id).order_by('name')
    return queryset