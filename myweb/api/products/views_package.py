from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max, Sum
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

@package_router.get("/", response=List[PackageOut])
@paginate(DefaultPagination)
def list_packages(
    request, 
    search: PackageSearchParams = Query(...)
):
    """
    Lists all packages with advanced filtering and pagination.
    Supports filtering by name, price range, rating, and product type.
    """
    try:
        queryset = Packages.objects.active()
        
        # Apply search filters with validation
        if search.name:
            queryset = queryset.filter(name__icontains=search.name)
        
        if search.min_price is not None:
            if search.min_price < 0:
                raise HttpError(422, "El precio mínimo no puede ser negativo")
            queryset = queryset.filter(final_price__gte=search.min_price)
        
        if search.max_price is not None:
            if search.max_price < 0:
                raise HttpError(422, "El precio máximo no puede ser negativo")
            queryset = queryset.filter(final_price__lte=search.max_price)
        
        if search.min_rating is not None:
            if not (0 <= search.min_rating <= 5):
                raise HttpError(422, "El rating mínimo debe estar entre 0 y 5")
            queryset = queryset.filter(rating_average__gte=search.min_rating)
        
        if search.max_rating is not None:
            if not (0 <= search.max_rating <= 5):
                raise HttpError(422, "El rating máximo debe estar entre 0 y 5")
            queryset = queryset.filter(rating_average__lte=search.max_rating)
        
        if search.is_active is not None:
            queryset = queryset.filter(is_active=search.is_active)
        
        if search.product_type:
            # Filter by product type in components with validation
            valid_types = ["activity", "flight", "lodgment", "transportation"]
            if search.product_type not in valid_types:
                raise HttpError(422, f"Tipo de producto inválido. Debe ser uno de: {', '.join(valid_types)}")
            
            queryset = queryset.filter(
                componentpackages__product_metadata__product_type=search.product_type
            ).distinct()
        
        # Order by name for consistency
        queryset = queryset.order_by('name')
        
        return queryset
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Error al listar paquetes: {str(e)}")


@package_router.get("/{package_id}", response=PackageDetailOut)
def get_package(request, package_id: int):
    """
    Gets a specific package with all its components and detailed information.
    Includes category data and component details.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        
        # Get ordered components with validation
        components = package.componentpackages.all().order_by('order')
        
        # Prepare component data for the response with error handling
        component_data = []
        for comp in components:
            try:
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
            except Exception as e:
                # Log error but continue with other components
                print(f"Error processing component {comp.id}: {e}")
                continue
        
        # Prepare category data
        category_data = None
        if package.category:
            try:
                category_data = {
                    "id": package.category.id,
                    "name": package.category.name,
                    "description": package.category.description,
                    "icon": package.category.icon,
                    "is_active": package.category.is_active,
                    "created_at": package.category.created_at,
                    "updated_at": package.category.updated_at
                }
            except Exception as e:
                print(f"Error processing category: {e}")
        
        return {
            **PackageOut.from_orm(package).dict(),
            "category": category_data,
            "components": component_data
        }
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except Exception as e:
        raise HttpError(500, f"Error al obtener paquete: {str(e)}")


@package_router.post("/", response=PackageDetailOut)
@transaction.atomic
def create_package(request, data: PackageCompleteCreate):
    """
    Creates a new package with its components in a single atomic transaction.
    Validates all data before creation and handles component relationships.
    """
    try:
        # Validate package data
        package_data = data.dict(exclude={'components'})
        
        # Handle cover_image field if None
        if package_data.get('cover_image') is None:
            package_data['cover_image'] = ""
        
        # Validate final price
        if package_data.get('final_price', 0) <= 0:
            raise HttpError(422, "El precio final debe ser mayor a 0")
        
        # Create the package with validation
        package = Packages(**package_data)
        package.full_clean()
        package.save()
        
        # Create the components with validation
        for i, comp_data in enumerate(data.components):
            try:
                # Validate component data
                component_data = comp_data.dict()
                
                # Validate product metadata exists
                product_metadata = get_object_or_404(
                    ProductsMetadata, 
                    id=component_data['product_metadata_id']
                )
                
                # Validate order is unique within package
                if ComponentPackages.objects.filter(
                    package=package, 
                    order=component_data.get('order', i)
                ).exists():
                    raise HttpError(422, f"El orden {component_data.get('order', i)} ya existe en este paquete")
                
                component = ComponentPackages.objects.create(
                    package=package,
                    **component_data
                )
                component.full_clean()
                component.save()
                
            except ValidationError as e:
                error_messages = []
                for field, errors in e.message_dict.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                error_detail = "; ".join(error_messages)
                raise HttpError(422, f"Error en componente {i+1}: {error_detail}")
            except Exception as e:
                raise HttpError(422, f"Error al crear componente {i+1}: {str(e)}")
        
        # Return the created package with its components
        return get_package(request, package.id)
        
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al crear paquete: {str(e)}")


@package_router.put("/{package_id}", response=PackageDetailOut)
@transaction.atomic
def update_package(request, package_id: int, data: PackageUpdate):
    """
    Updates an existing package with validation and atomic transaction.
    Only updates provided fields and validates all constraints.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        
        # Update package fields with validation
        update_data = data.dict(exclude_unset=True)
        
        # Validate final price if provided
        if 'final_price' in update_data and update_data['final_price'] <= 0:
            raise HttpError(422, "El precio final debe ser mayor a 0")
        
        for field, value in update_data.items():
            setattr(package, field, value)
        
        # Validate the updated package
        package.full_clean()
        package.save()
        
        return get_package(request, package.id)
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al actualizar paquete: {str(e)}")


@package_router.delete("/{package_id}")
@transaction.atomic
def delete_package(request, package_id: int):
    """
    Soft deletes a package by setting is_active=False and deleted_at timestamp.
    Uses atomic transaction for data consistency.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        
        # Check if package has active orders (if applicable)
        # This could be extended to check for dependencies
        
        package.is_active = False
        package.deleted_at = timezone.now()
        package.save()
        
        return {"message": "Paquete eliminado exitosamente", "package_id": package_id}
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except Exception as e:
        raise HttpError(500, f"Error al eliminar paquete: {str(e)}")


# ──────────────────────────────────────────────────────────────
# PACKAGE COMPONENTS ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/{package_id}/components", response=List[ComponentPackageOut])
def list_package_components(request, package_id: int):
    """
    Lists all components of a specific package with detailed information.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        components = package.componentpackages.all().order_by('order')
        return [ComponentPackageOut.from_orm(comp) for comp in components]
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except Exception as e:
        raise HttpError(500, f"Error al listar componentes: {str(e)}")


@package_router.post("/{package_id}/components", response=ComponentPackageOut)
@transaction.atomic
def add_package_component(request, package_id: int, data: ComponentPackageCreate):
    """
    Adds a new component to a package with validation and atomic transaction.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        
        # Validate component data
        component_data = data.dict()
        
        # Validate product metadata exists
        product_metadata = get_object_or_404(
            ProductsMetadata, 
            id=component_data['product_metadata_id']
        )
        
        # Validate order is unique within package
        if ComponentPackages.objects.filter(
            package=package, 
            order=component_data.get('order', 0)
        ).exists():
            raise HttpError(422, f"El orden {component_data.get('order', 0)} ya existe en este paquete")
        
        # Create component with validation
        component = ComponentPackages.objects.create(
            package=package,
            **component_data
        )
        component.full_clean()
        component.save()
        
        return ComponentPackageOut.from_orm(component)
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except ProductsMetadata.DoesNotExist:
        raise HttpError(404, "Producto no encontrado")
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al agregar componente: {str(e)}")


@package_router.put("/{package_id}/components/{component_id}", response=ComponentPackageOut)
@transaction.atomic
def update_package_component(
    request, 
    package_id: int, 
    component_id: int, 
    data: ComponentPackageUpdate
):
    """
    Updates a specific component of a package with validation.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        component = get_object_or_404(ComponentPackages, id=component_id, package=package)
        
        # Update component fields with validation
        update_data = data.dict(exclude_unset=True)
        
        # Validate order uniqueness if order is being updated
        if 'order' in update_data:
            if ComponentPackages.objects.filter(
                package=package, 
                order=update_data['order']
            ).exclude(id=component_id).exists():
                raise HttpError(422, f"El orden {update_data['order']} ya existe en este paquete")
        
        for field, value in update_data.items():
            setattr(component, field, value)
        
        component.full_clean()
        component.save()
        return ComponentPackageOut.from_orm(component)
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except ComponentPackages.DoesNotExist:
        raise HttpError(404, "Componente no encontrado")
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al actualizar componente: {str(e)}")


@package_router.delete("/{package_id}/components/{component_id}")
@transaction.atomic
def remove_package_component(request, package_id: int, component_id: int):
    """
    Removes a component from a package with atomic transaction.
    """
    try:
        package = get_object_or_404(Packages.objects.active(), id=package_id)
        component = get_object_or_404(ComponentPackages, id=component_id, package=package)
        
        component.delete()
        return {"message": "Componente eliminado exitosamente", "component_id": component_id}
        
    except Packages.DoesNotExist:
        raise HttpError(404, "Paquete no encontrado")
    except ComponentPackages.DoesNotExist:
        raise HttpError(404, "Componente no encontrado")
    except Exception as e:
        raise HttpError(500, f"Error al eliminar componente: {str(e)}")


# ──────────────────────────────────────────────────────────────
# SEARCH AND FILTER ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/search/featured", response=List[PackageOut])
def get_featured_packages(request, limit: int = 10):
    """
    Gets featured packages with high rating and active status.
    Includes validation for limit parameter.
    """
    try:
        if limit <= 0 or limit > 100:
            raise HttpError(422, "El límite debe estar entre 1 y 100")
        
        packages = Packages.objects.active().filter(
            rating_average__gte=4.0,
            is_active=True
        ).order_by('-rating_average', '-total_reviews')[:limit]
        
        return [PackageOut.from_orm(pkg) for pkg in packages]
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Error al obtener paquetes destacados: {str(e)}")


@package_router.get("/search/by-price-range", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_price_range(
    request, 
    min_price: float, 
    max_price: float
):
    """
    Gets packages within a specific price range with validation.
    """
    try:
        if min_price < 0:
            raise HttpError(422, "El precio mínimo no puede ser negativo")
        if max_price < 0:
            raise HttpError(422, "El precio máximo no puede ser negativo")
        if min_price > max_price:
            raise HttpError(422, "El precio mínimo no puede ser mayor al precio máximo")
        
        packages = Packages.objects.active().filter(
            final_price__gte=min_price,
            final_price__lte=max_price
        ).order_by('final_price')
        
        return packages
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Error al buscar por rango de precio: {str(e)}")


@package_router.get("/search/by-duration", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_duration(
    request, 
    min_days: int, 
    max_days: int
):
    """
    Gets packages within a specific duration range.
    Note: This is a simplified implementation that could be enhanced.
    """
    try:
        if min_days < 1:
            raise HttpError(422, "La duración mínima debe ser al menos 1 día")
        if max_days < min_days:
            raise HttpError(422, "La duración máxima no puede ser menor a la mínima")
        
        # This would need a more complex query to calculate duration
        # For now, returning all packages
        packages = Packages.objects.active().order_by('name')
        return packages
        
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Error al buscar por duración: {str(e)}")


# ──────────────────────────────────────────────────────────────
# STATISTICS ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/stats/overview")
def get_packages_stats(request):
    """
    Gets comprehensive overview statistics for packages.
    Includes error handling and data validation.
    """
    try:
        # Basic counts
        total_packages = Packages.objects.active().count()
        active_packages = Packages.objects.filter(is_active=True).count()
        
        # Rating statistics
        rating_stats = Packages.objects.active().aggregate(
            avg_rating=Avg('rating_average'),
            max_rating=Max('rating_average'),
            min_rating=Min('rating_average'),
            total_with_ratings=Count('rating_average', filter=Q(rating_average__gt=0))
        )
        
        # Price statistics
        price_stats = Packages.objects.active().aggregate(
            avg_price=Avg('final_price'),
            max_price=Max('final_price'),
            min_price=Min('final_price'),
            total_revenue=Sum('final_price')
        )
        
        # Category statistics
        category_stats = Packages.objects.active().values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            "total_packages": total_packages,
            "active_packages": active_packages,
            "inactive_packages": total_packages - active_packages,
            "rating_stats": {
                "average": round(rating_stats['avg_rating'] or 0, 2),
                "maximum": rating_stats['max_rating'] or 0,
                "minimum": rating_stats['min_rating'] or 0,
                "packages_with_ratings": rating_stats['total_with_ratings']
            },
            "price_stats": {
                "average": round(price_stats['avg_price'] or 0, 2),
                "maximum": price_stats['max_price'] or 0,
                "minimum": price_stats['min_price'] or 0,
                "total_revenue": round(price_stats['total_revenue'] or 0, 2)
            },
            "top_categories": [
                {"name": stat['category__name'] or "Sin categoría", "count": stat['count']}
                for stat in category_stats
            ]
        }
        
    except Exception as e:
        raise HttpError(500, f"Error al obtener estadísticas: {str(e)}")


# ──────────────────────────────────────────────────────────────
# CATEGORY ENDPOINTS
# ──────────────────────────────────────────────────────────────

@category_router.get("/", response=List[CategoryOut])
def list_categories(request):
    """
    Lists all active categories with error handling.
    """
    try:
        categories = Category.objects.active().order_by('name')
        return [CategoryOut.from_orm(cat) for cat in categories]
        
    except Exception as e:
        raise HttpError(500, f"Error al listar categorías: {str(e)}")


@category_router.get("/{category_id}", response=CategoryOut)
def get_category(request, category_id: int):
    """
    Gets a specific category with validation.
    """
    try:
        category = get_object_or_404(Category.objects.active(), id=category_id)
        return CategoryOut.from_orm(category)
        
    except Category.DoesNotExist:
        raise HttpError(404, "Categoría no encontrada")
    except Exception as e:
        raise HttpError(500, f"Error al obtener categoría: {str(e)}")


@category_router.post("/", response=CategoryOut)
@transaction.atomic
def create_category(request, data: CategoryCreate):
    """
    Creates a new category with validation and atomic transaction.
    """
    try:
        # Validate category data
        category_data = data.dict()
        
        # Check for duplicate names
        if Category.objects.filter(name=category_data['name']).exists():
            raise HttpError(422, "Ya existe una categoría con ese nombre")
        
        category = Category.objects.create(**category_data)
        category.full_clean()
        category.save()
        
        return CategoryOut.from_orm(category)
        
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al crear categoría: {str(e)}")


@category_router.put("/{category_id}", response=CategoryOut)
@transaction.atomic
def update_category(request, category_id: int, data: CategoryUpdate):
    """
    Updates an existing category with validation.
    """
    try:
        category = get_object_or_404(Category.objects.active(), id=category_id)
        
        update_data = data.dict(exclude_unset=True)
        
        # Check for duplicate names if name is being updated
        if 'name' in update_data:
            if Category.objects.filter(name=update_data['name']).exclude(id=category_id).exists():
                raise HttpError(422, "Ya existe una categoría con ese nombre")
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        category.full_clean()
        category.save()
        return CategoryOut.from_orm(category)
        
    except Category.DoesNotExist:
        raise HttpError(404, "Categoría no encontrada")
    except HttpError:
        raise
    except ValidationError as e:
        error_messages = []
        for field, errors in e.message_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        error_detail = "; ".join(error_messages)
        raise HttpError(422, f"Error de validación: {error_detail}")
    except Exception as e:
        raise HttpError(500, f"Error al actualizar categoría: {str(e)}")


@category_router.delete("/{category_id}")
@transaction.atomic
def delete_category(request, category_id: int):
    """
    Soft deletes a category with dependency checking.
    """
    try:
        category = get_object_or_404(Category.objects.active(), id=category_id)
        
        # Check if category has packages
        package_count = Packages.objects.filter(category=category, is_active=True).count()
        if package_count > 0:
            raise HttpError(422, f"No se puede eliminar la categoría porque tiene {package_count} paquetes activos")
        
        category.is_active = False
        category.save()
        
        return {"message": "Categoría eliminada exitosamente", "category_id": category_id}
        
    except Category.DoesNotExist:
        raise HttpError(404, "Categoría no encontrada")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(500, f"Error al eliminar categoría: {str(e)}")


# ──────────────────────────────────────────────────────────────
# CATEGORY-PACKAGE RELATIONSHIP ENDPOINTS
# ──────────────────────────────────────────────────────────────

@package_router.get("/{category_id}/packages", response=List[PackageOut])
@paginate(DefaultPagination)
def get_packages_by_category(request, category_id: int):
    """
    Gets all packages for a specific category with validation.
    """
    try:
        category = get_object_or_404(Category.objects.active(), id=category_id)
        packages = Packages.objects.active().filter(category=category).order_by('name')
        return packages
        
    except Category.DoesNotExist:
        raise HttpError(404, "Categoría no encontrada")
    except Exception as e:
        raise HttpError(500, f"Error al obtener paquetes de categoría: {str(e)}")