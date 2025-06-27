from ninja import Router

# Si tienes un modelo llamado Package, descomenta la siguiente línea:
# from .models import Package

# Si tienes un schema para la salida, descomenta la siguiente línea:
# from .schemas import PackageOut

package_router = Router(tags=["Paquetes"])

@package_router.get("/paquetes/", response=list)
def listar_paquetes(request):
    """
    Endpoint básico para listar paquetes.
    Reemplaza la lista de ejemplo por una consulta real a tu modelo.
    """
    paquetes = [
        {"id": 1, "nombre": "Paquete A"},
        {"id": 2, "nombre": "Paquete B"},
    ]
    return paquetes

# Puedes agregar más endpoints aquí, por ejemplo:
# - Crear paquete
# - Obtener paquete por ID
# - Actualizar paquete
# - Eliminar paquete