from django.core.management.base import BaseCommand, CommandError
from ip_tracking.models import BlockedIP


class Command(BaseCommand):
    help = 'Unblock an IP address to allow access to the site'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'ip_address',
            type=str,
            help='The IP address to unblock'
        )
    
    def handle(self, *args, **options):
        ip_address = options['ip_address']
        
        try:
            # Try to find and delete the blocked IP
            blocked_ip = BlockedIP.objects.filter(ip_address=ip_address).first()
            
            if blocked_ip:
                blocked_ip.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully unblocked IP address: {ip_address}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'IP address {ip_address} is not currently blocked.'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Failed to unblock IP {ip_address}: {e}')
