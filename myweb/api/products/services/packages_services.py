from django.db.models.query import QuerySet

from typing import List, Any, Dict

from .stock_services import (
    check_activity_stock,
    check_room_stock,
    check_flight_stock,
    check_transportation_stock, ProductNotFoundError
)

from ..models import (
    ComponentPackages,
    Packages,
    ProductsMetadata,
    Activities, Lodgments, Transportation, Flights
)

class PackagesServiceInterface:
    @staticmethod
    def get_packages_filtered_by_availability(query_set: QuerySet) -> List[Packages] | None:
        pks_list = []
        for pkg in query_set:
            components = PackagesServiceInterface.get_package_components(pkg)
            for type_, com in components.items():
                match type_:
                    case 'activity':
                        try:
                            data = check_activity_stock(com['avail_id'], com['qty'])
                            if data['sufficient']:
                                pks_list.append(pkg)
                            else:
                                continue
                        except ProductNotFoundError:
                            continue

                    case 'lodgment':
                        try:
                            data = check_room_stock(com['avail_id'], com['qty'])
                            if data['sufficient']:
                                pks_list.append(pkg)
                            else:
                                continue
                        except ProductNotFoundError:
                            continue

                    case 'flight':
                        try:
                            data = check_flight_stock(com['avail_id'], com['qty'])
                            if data['sufficient']:
                                pks_list.append(pkg)
                            else:
                                continue
                        except ProductNotFoundError:
                            continue

                    case 'transportation':
                        try:
                            data = check_transportation_stock(com['avail_id'], com['qty'])
                            if data['sufficient']:
                                pks_list.append(pkg)
                            else:
                                continue
                        except ProductNotFoundError:
                            continue
        return pks_list






    @staticmethod
    def get_package_components(package: Packages) -> Dict[str, Dict[str, Activities] | Dict[str, Lodgments] | Dict[str, Transportation] | Dict[str, Flights] | Dict[str, Any]] | Dict:
        component_packages: List[ComponentPackages] = ComponentPackages.objects.filter(package_id=package.id).all()
        components = {}
        for com in component_packages:
            for meta in com.metadata_per_product:
                product = meta.get_content_object
                components.setdefault(meta.product_type, {
                    "avail_id": com.availability_id,
                    "product": product,
                    "qty": com.quantity
                })

        return components