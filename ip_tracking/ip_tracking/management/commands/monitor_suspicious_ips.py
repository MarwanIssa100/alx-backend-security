from django.core.management.base import BaseCommand
from django.utils import timezone
from ip_tracking.tasks import monitor_suspicious_ips, cleanup_old_suspicious_flags, auto_block_suspicious_ips


class Command(BaseCommand):
    help = 'Manually trigger suspicious IP monitoring and related tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['monitor', 'cleanup', 'auto-block', 'all'],
            default='all',
            help='Which task to run (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually running the task'
        )
    
    def handle(self, *args, **options):
        task = options['task']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No tasks will actually be executed')
            )
        
        if task == 'monitor' or task == 'all':
            self.run_monitoring_task(dry_run)
        
        if task == 'cleanup' or task == 'all':
            self.run_cleanup_task(dry_run)
        
        if task == 'auto-block' or task == 'all':
            self.run_auto_block_task(dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('Task execution completed successfully!')
        )
    
    def run_monitoring_task(self, dry_run):
        """Run the suspicious IP monitoring task."""
        self.stdout.write('\nRunning Suspicious IP Monitoring Task...')
        
        if dry_run:
            self.stdout.write('Would run: monitor_suspicious_ips()')
            return
        
        try:
            result = monitor_suspicious_ips()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Monitoring task completed successfully!\n'
                    f'Results: {result}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running monitoring task: {e}')
            )
    
    def run_cleanup_task(self, dry_run):
        """Run the cleanup task for old suspicious flags."""
        self.stdout.write('\nRunning Cleanup Task for Old Suspicious Flags...')
        
        if dry_run:
            self.stdout.write('Would run: cleanup_old_suspicious_flags()')
            return
        
        try:
            result = cleanup_old_suspicious_flags()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup task completed successfully!\n'
                    f'Results: {result}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running cleanup task: {e}')
            )
    
    def run_auto_block_task(self, dry_run):
        """Run the auto-block task for severely suspicious IPs."""
        self.stdout.write('\nRunning Auto-Block Task for Severely Suspicious IPs...')
        
        if dry_run:
            self.stdout.write('Would run: auto_block_suspicious_ips()')
            return
        
        try:
            result = auto_block_suspicious_ips()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Auto-block task completed successfully!\n'
                    f'Results: {result}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running auto-block task: {e}')
            )
