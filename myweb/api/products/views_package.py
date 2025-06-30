from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import List
from datetime import date

from .models import Packages, ComponentPackages, ProductsMetadata, Category
from .schemas import (
    PackageCreate, PackageUpdate, PackageOut, PackageDetailOut, PackageSearchParams,
    ComponentPackageCreate, ComponentPackageUpdate, ComponentPackageOut,
    PackageCompleteCreate, CategoryCreate, CategoryUpdate, CategoryOut
)
from .pagination import PaginationParams, paginate_response

package_router = Router(tags=["Paquetes"])
category_router = Router(tags=["Categorías"])
# ──────────────────────────────────────────────────────────────
# ENDPOINTS PRINCIPALES DE PAQUETES
# ──────────────────────────────────────────────────────────────

@package_router.get("/", response=List[PackageOut])
def list_packages(
    request, 
    pagination: PaginationParams = Query(...),
    search: PackageSearchParams = Query(...)
):
    """
    Lista todos los paquetes con filtros y paginación
    """
    queryset = Packages.active.all()
    
    # Aplicar filtros de búsqueda
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
        # Filtrar por tipo de producto en los componentes
        queryset = queryset.filter(
            componentpackages__product_metadata__product_type=search.product_type
        ).distinct()
    
    # Ordenar por nombre
    queryset = queryset.order_by('name')
    
    # Convertir a lista de schemas antes de paginar
    packages = [PackageOut.from_orm(pkg) for pkg in queryset]
    
    return paginate_response(packages, pagination)


@package_router.get("/{package_id}", response=PackageDetailOut)
def get_package(request, package_id: int):
    """
    Obtiene un paquete específico con todos sus componentes
    """
    package = get_object_or_404(Packages.active, id=package_id)
    
    # Obtener componentes ordenados
    components = package.componentpackages.all().order_by('order')
    
    # Preparar datos de componentes para la respuesta
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
    
    # Preparar datos de la categoría
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
def create_package(request, data: PackageCompleteCreate):
    """
    Crea un nuevo paquete con sus componentes
    """
    try:
        # Crear el paquete
        package_data = data.dict(exclude={'components'})
        
        # Manejar el campo cover_image si es None
        if package_data.get('cover_image') is None:
            package_data['cover_image'] = ""  # Establecer string vacío en lugar de None
        
        package = Packages.objects.create(**package_data)
        
        # Crear los componentes
        for comp_data in data.components:
            ComponentPackages.objects.create(
                package=package,
                **comp_data.dict()
            )
        
        # Retornar el paquete creado con sus componentes
        return get_package(request, package.id)
        
    except ValidationError as e:
        raise ValidationError(f"Error de validación: {e}")
    except Exception as e:
        raise ValidationError(f"Error al crear el paquete: {e}")


@package_router.put("/{package_id}", response=PackageDetailOut)
def update_package(request, package_id: int, data: PackageUpdate):
    """
    Actualiza un paquete existente
    """
    package = get_object_or_404(Packages.active, id=package_id)
    
    try:
        # Actualizar campos del paquete
        for field, value in data.dict(exclude_unset=True).items():
            setattr(package, field, value)
        
        package.full_clean()
        package.save()
        
        return get_package(request, package.id)
        
    except ValidationError as e:
        raise ValidationError(f"Error de validación: {e}")
    except Exception as e:
        raise ValidationError(f"Error al actualizar el paquete: {e}")


@package_router.delete("/{package_id}")
def delete_package(request, package_id: int):
    """
    Elimina (soft delete) un paquete
    """
    package = get_object_or_404(Packages.active, id=package_id)
    
    try:
        package.is_active = False
        package.deleted_at = timezone.now()
        package.save()
        
        return {"message": "Paquete eliminado correctamente"}
        
    except Exception as e:
        raise ValidationError(f"Error al eliminar el paquete: {e}")


# ──────────────────────────────────────────────────────────────
# ENDPOINTS DE COMPONENTES DE PAQUETES
# ──────────────────────────────────────────────────────────────

@package_router.get("/{package_id}/components", response=List[ComponentPackageOut])
def list_package_components(request, package_id: int):
    """
    Lista todos los componentes de un paquete específico
    """
    package = get_object_or_404(Packages.active, id=package_id)
    components = package.componentpackages.all().order_by('order')
    
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
    
    return component_data


@package_router.post("/{package_id}/components", response=ComponentPackageOut)
def add_package_component(request, package_id: int, data: ComponentPackageCreate):
    """
    Agrega un nuevo componente a un paquete
    """
    package = get_object_or_404(Packages.active, id=package_id)
    
    try:
        # Verificar que el product_metadata existe
        product_metadata = get_object_or_404(ProductsMetadata, id=data.product_metadata_id)
        
        # Crear el componente
        component = ComponentPackages.objects.create(
            package=package,
            **data.dict()
        )
        
        return {
            "id": component.id,
            "product_metadata_id": component.product_metadata_id,
            "order": component.order,
            "quantity": component.quantity,
            "title": component.title,
            "start_date": component.start_date,
            "end_date": component.end_date,
            "product_type": component.product_metadata.product_type,
            "product_name": str(component.product_metadata.content)
        }
        
    except ValidationError as e:
        raise ValidationError(f"Error de validación: {e}")
    except Exception as e:
        raise ValidationError(f"Error al agregar el componente: {e}")


@package_router.put("/{package_id}/components/{component_id}", response=ComponentPackageOut)
def update_package_component(
    request, 
    package_id: int, 
    component_id: int, 
    data: ComponentPackageUpdate
):
    """
    Actualiza un componente específico de un paquete
    """
    package = get_object_or_404(Packages.active, id=package_id)
    component = get_object_or_404(ComponentPackages, id=component_id, package=package)
    
    try:
        # Actualizar campos del componente
        for field, value in data.dict(exclude_unset=True).items():
            setattr(component, field, value)
        
        component.full_clean()
        component.save()
        
        return {
            "id": component.id,
            "product_metadata_id": component.product_metadata_id,
            "order": component.order,
            "quantity": component.quantity,
            "title": component.title,
            "start_date": component.start_date,
            "end_date": component.end_date,
            "product_type": component.product_metadata.product_type,
            "product_name": str(component.product_metadata.content)
        }
        
    except ValidationError as e:
        raise ValidationError(f"Error de validación: {e}")
    except Exception as e:
        raise ValidationError(f"Error al actualizar el componente: {e}")


@package_router.delete("/{package_id}/components/{component_id}")
def remove_package_component(request, package_id: int, component_id: int):
    """
    Elimina un componente específico de un paquete
    """
    package = get_object_or_404(Packages.active, id=package_id)
    component = get_object_or_404(ComponentPackages, id=component_id, package=package)
    
    try:
        component.delete()
        return {"message": "Componente eliminado correctamente"}
        
    except Exception as e:
        raise ValidationError(f"Error al eliminar el componente: {e}")


# ──────────────────────────────────────────────────────────────
# ENDPOINTS DE BÚSQUEDA Y FILTROS ESPECIALES
# ──────────────────────────────────────────────────────────────

@package_router.get("/search/featured", response=List[PackageOut])
def get_featured_packages(request, limit: int = 10):
    """
    Obtiene los paquetes destacados (con mejor rating)
    """
    packages = Packages.active.filter(
        rating_average__gt=0,
        total_reviews__gt=0
    ).order_by('-rating_average', '-total_reviews')[:limit]
    
    return [PackageOut.from_orm(pkg) for pkg in packages]


@package_router.get("/search/by-price-range", response=List[PackageOut])
def get_packages_by_price_range(
    request, 
    min_price: float, 
    max_price: float,
    pagination: PaginationParams = Query(...)
):
    """
    Busca paquetes por rango de precio
    """
    queryset = Packages.active.filter(
        final_price__gte=min_price,
        final_price__lte=max_price
    ).order_by('final_price')
    
    return paginate_response(queryset, pagination)


@package_router.get("/search/by-duration", response=List[PackageOut])
def get_packages_by_duration(
    request, 
    min_days: int, 
    max_days: int,
    pagination: PaginationParams = Query(...)
):
    """
    Busca paquetes por duración (calculada automáticamente)
    """
    # Nota: Esta implementación es básica, podrías optimizarla
    # calculando la duración en la base de datos
    packages = Packages.active.all()
    
    filtered_packages = []
    for package in packages:
        duration = package.duration_days
        if duration and min_days <= duration <= max_days:
            filtered_packages.append(package)
    
    # Aplicar paginación manual
    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size
    paginated_packages = filtered_packages[start:end]
    
    return [PackageOut.from_orm(pkg) for pkg in paginated_packages]


# ──────────────────────────────────────────────────────────────
# ENDPOINTS DE ESTADÍSTICAS
# ──────────────────────────────────────────────────────────────

@package_router.get("/stats/overview")
def get_packages_stats(request):
    """
    Obtiene estadísticas generales de los paquetes
    """
    total_packages = Packages.active.count()
    active_packages = Packages.active.filter(is_active=True).count()
    
    # Estadísticas de precios
    price_stats = Packages.active.aggregate(
        avg_price=Avg('final_price'),
        min_price=Min('final_price'),
        max_price=Max('final_price')
    )
    
    # Estadísticas de rating
    rating_stats = Packages.active.filter(rating_average__gt=0).aggregate(
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
# ENDPOINTS DE CATEGORÍAS
# ──────────────────────────────────────────────────────────────

@category_router.get("/", response=List[CategoryOut])
def list_categories(request):
    """
    Lista todas las categorías activas
    """
    categories = Category.active.all().order_by('name')
    return [CategoryOut.from_orm(cat) for cat in categories]


@category_router.get("/{category_id}", response=CategoryOut)
def get_category(request, category_id: int):
    """
    Obtiene una categoría específica
    """
    category = get_object_or_404(Category.active, id=category_id)
    return CategoryOut.from_orm(category)


@category_router.post("/", response=CategoryOut)
def create_category(request, data: CategoryCreate):
    """
    Crea una nueva categoría
    """
    try:
        category = Category.objects.create(**data.dict())
        return CategoryOut.from_orm(category)
    except Exception as e:
        raise ValidationError(f"Error al crear la categoría: {e}")


@category_router.put("/{category_id}", response=CategoryOut)
def update_category(request, category_id: int, data: CategoryUpdate):
    """
    Actualiza una categoría existente
    """
    category = get_object_or_404(Category.active, id=category_id)
    
    try:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(category, field, value)
        
        category.full_clean()
        category.save()
        
        return CategoryOut.from_orm(category)
    except Exception as e:
        raise ValidationError(f"Error al actualizar la categoría: {e}")


@category_router.delete("/{category_id}")
def delete_category(request, category_id: int):
    """
    Elimina (soft delete) una categoría
    """
    category = get_object_or_404(Category.active, id=category_id)
    
    try:
        category.is_active = False
        category.save()
        
        return {"message": "Categoría eliminada correctamente"}
    except Exception as e:
        raise ValidationError(f"Error al eliminar la categoría: {e}")


@category_router.get("/{category_id}/packages", response=List[PackageOut])
def get_packages_by_category(request, category_id: int, pagination: PaginationParams = Query(...)):
    """
    Obtiene todos los paquetes de una categoría específica
    """
    category = get_object_or_404(Category.active, id=category_id)
    packages = Packages.active.filter(category=category).order_by('name')
    
    return paginate_response(packages, pagination)