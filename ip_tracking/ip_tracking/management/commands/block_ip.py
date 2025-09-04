from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ip_tracking.models import BlockedIP


class Command(BaseCommand):
    help = 'Block an IP address from accessing the site'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'ip_address',
            type=str,
            help='The IP address to block'
        )
        parser.add_argument(
            '--reason',
            type=str,
            default='',
            help='Optional reason for blocking this IP'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update if IP already exists'
        )
    
    def handle(self, *args, **options):
        ip_address = options['ip_address']
        reason = options['reason']
        force = options['force']
        
        try:
            # Check if IP already exists
            blocked_ip, created = BlockedIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'reason': reason,
                    'created_at': timezone.now()
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully blocked IP address: {ip_address}'
                    )
                )
            else:
                if force:
                    # Update existing blocked IP
                    blocked_ip.reason = reason
                    blocked_ip.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated blocked IP address: {ip_address}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'IP address {ip_address} is already blocked. '
                            f'Use --force to update.'
                        )
                    )
                    return
                
        except Exception as e:
            raise CommandError(f'Failed to block IP {ip_address}: {e}')
        
        # Display the blocked IP details
        self.stdout.write(
            f'IP Address: {blocked_ip.ip_address}\n'
            f'Blocked At: {blocked_ip.created_at}\n'
            f'Reason: {blocked_ip.reason or "No reason provided"}'
        )
