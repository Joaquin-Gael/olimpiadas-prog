from django.core.management.base import BaseCommand
from django.utils import timezone, timedelta
from api.store.models import StoreIdempotencyRecord


class Command(BaseCommand):
    help = 'Limpia registros de idempotencia antiguos (más de 48 horas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=48,
            help='Horas de antigüedad para considerar un registro como obsoleto (default: 48)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cuántos registros se eliminarían sin ejecutar la eliminación'
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        
        if options['dry_run']:
            count = StoreIdempotencyRecord.objects.filter(created_at__lt=cutoff).count()
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Se eliminarían {count} registros de idempotencia '
                    f'creados antes de {cutoff}'
                )
            )
            return

        deleted_count = StoreIdempotencyRecord.objects.filter(
            created_at__lt=cutoff
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se eliminaron {deleted_count} registros de idempotencia '
                f'creados antes de {cutoff}'
            )
        ) 