from .schemas import (
    ProductsMetadataOut,
    ActivityOut,
    FlightOut,
    LodgmentOut,
    TransportationOut
)
from .models import ProductsMetadata

def serialize_product_metadata(metadata: ProductsMetadata) -> ProductsMetadataOut:
    tipo = metadata.tipo_producto
    producto = metadata.content  # instancia real del modelo relacionado

    if tipo == "actividad":
        producto_schema = ActivityOut.from_orm(producto)
    elif tipo == "vuelo":
        producto_schema = FlightOut.from_orm(producto)
    elif tipo == "alojamiento":
        producto_schema = LodgmentOut.from_orm(producto)
    elif tipo == "transporte":
        producto_schema = TransportationOut.from_orm(producto)
    else:
        raise ValueError("Tipo de product no reconocido")

    return ProductsMetadataOut(
        id=metadata.id,
        precio_unitario=metadata.precio_unitario,
        product_type=tipo,
        producto=producto_schema
    )