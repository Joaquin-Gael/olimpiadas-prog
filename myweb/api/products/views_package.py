from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError

from typing import List

from django.shortcuts import get_list_or_404

from .models import Packages

from .schemas import PackageOut

package_router = Router(tags=["Packages"])

@package_router.get("/", response={200:List[PackageOut]})
def list_packages(request):
    """
    Endpoint básico para listar paquetes.
    Reemplaza la lista de ejemplo por una consulta real a tu modelo.
    """
    try:
        _list_packages: List[Packages] | None = get_list_or_404(Packages)

        serialized_packages = []
        for i in _list_packages:
            serialized_packages.append(
                PackageOut.from_orm(i)
            )

        return Response(serialized_packages)

    except Exception as e:
        raise HttpError(status_code=500, message="No se ha podido realizar la lista: {}".format(e))

# Puedes agregar más endpoints aquí, por ejemplo:
# - Crear paquete
# - Obtener paquete por ID
# - Actualizar paquete
# - Eliminar paquete