from ninja import Router
from .schemas import ProductsMetadataOut, PackageCreate, PackageOut
from .helpers import serialize_product_metadata, serialize_package
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import (
    ProductsMetadata, Suppliers,
    Activities, Flights, Lodgments, Transportation
)

router = Router(tags=["Productos"]) 

@router.post("/productos/crear/", response=ProductsMetadataOut)
def crear_producto(request, data: ProductsMetadataCreate):
    supplier = get_object_or_404(Suppliers, id=data.supplier_id)

    tipo = data.tipo_producto
    producto_creado = None

    # Crear el producto correspondiente
    if tipo == "actividad":
        producto_creado = Activities.objects.create(**data.producto.dict())
    elif tipo == "vuelo":
        producto_creado = Flights.objects.create(**data.producto.dict())
    elif tipo == "alojamiento":
        producto_creado = Lodgments.objects.create(**data.producto.dict())
    elif tipo == "transporte":
        producto_creado = Transportation.objects.create(**data.producto.dict())
    else:
        raise HttpError(400, "Tipo de producto no válido")

    # Crear metadata relacionada
    metadata = ProductsMetadata.objects.create(
        supplier=supplier,
        content_object=producto_creado,
        tipo_producto=tipo,
        precio_unitario=data.precio_unitario
    )

    # Devolver schema serializado
    return serialize_product_metadata(metadata)

@router.get("/productos/", response=list[ProductsMetadataOut])
def listar_productos(request):
    productos = ProductsMetadata.objects.select_related("content_type").all()
    return [serialize_product_metadata(p) for p in productos]


@router.get("/productos/{id}/", response=ProductsMetadataOut)
def obtener_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata.objects.select_related("content_type"), id=id)
    return serialize_product_metadata(metadata)

@router.put("/productos/{id}/", response=ProductsMetadataOut)
def actualizar_producto(request, id: int, data: ProductsMetadataCreate):
    metadata = get_object_or_404(ProductsMetadata, id=id)
    tipo = metadata.tipo_producto
    producto = metadata.content  # modelo real
    producto_data = data.producto.dict()

    # Actualizar los datos del producto real
    for attr, value in producto_data.items():
        setattr(producto, attr, value)
    producto.save()

    # También actualizamos el precio y tipo si cambia
    metadata.precio_unitario = data.precio_unitario
    metadata.tipo_producto = data.tipo_producto
    metadata.supplier_id = data.supplier_id
    metadata.save()

    return serialize_product_metadata(metadata)

@router.delete("/productos/{id}/", response={204: None})
def eliminar_producto(request, id: int):
    metadata = get_object_or_404(ProductsMetadata, id=id)
    producto = metadata.content

    try:
        producto.delete()  # elimina actividad/vuelo/etc.
        metadata.delete()  # elimina metadata asociada
    except Exception as e:
        raise HttpError(500, f"No se pudo eliminar el producto: {str(e)}")

    return 204  # sin contenido, éxito