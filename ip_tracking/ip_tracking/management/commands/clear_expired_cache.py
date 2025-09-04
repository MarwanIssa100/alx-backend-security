from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ip_tracking.models import IPGeolocationCache


class Command(BaseCommand):
    help = 'Clear expired IP geolocation cache entries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Cache entries older than this many hours will be cleared (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find expired cache entries
        expired_entries = IPGeolocationCache.objects.filter(cached_at__lt=cutoff_time)
        count = expired_entries.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No expired cache entries found (older than {hours} hours).')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} expired cache entries older than {hours} hours.'
                )
            )
            
            # Show some examples
            for entry in expired_entries[:5]:
                self.stdout.write(f'  - {entry.ip_address} (cached at {entry.cached_at})')
            
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more entries')
        else:
            # Actually delete expired entries
            expired_entries.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired cache entries older than {hours} hours.'
                )
            )
