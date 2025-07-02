from django.core.management.base import BaseCommand
from django.utils import timezone, timedelta
from api.store.models import Cart
from api.store.services import services_cart as cart_srv


class Command(BaseCommand):
    help = 'Expira carritos abiertos que no han sido actualizados en las últimas 24 horas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Horas de inactividad para considerar un carrito como expirado (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cuántos carritos se expirarían sin ejecutar la expiración'
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        
        expired_carts = Cart.objects.filter(
            status="OPEN",
            updated_at__lt=cutoff
        )
        
        if options['dry_run']:
            count = expired_carts.count()
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Se expirarían {count} carritos no actualizados '
                    f'desde hace más de {options["hours"]} horas'
                )
            )
            return

        expired_count = 0
        for cart in expired_carts:
            try:
                cart_srv.expire_cart(cart)
                expired_count += 1
                self.stdout.write(f'Carrito {cart.id} expirado')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al expirar carrito {cart.id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se expiraron {expired_count} carritos no actualizados '
                f'desde hace más de {options["hours"]} horas'
            )
        ) 