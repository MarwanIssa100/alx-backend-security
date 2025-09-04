import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ip_tracking.settings')

app = Celery('ip_tracking')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Configure Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'monitor-suspicious-ips-hourly': {
        'task': 'ip_tracking.tasks.monitor_suspicious_ips',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    'cleanup-old-suspicious-flags-daily': {
        'task': 'ip_tracking.tasks.cleanup_old_suspicious_flags',
        'schedule': 86400.0,  # Every day (86400 seconds)
    },
    'auto-block-severely-suspicious-ips-daily': {
        'task': 'ip_tracking.tasks.auto_block_suspicious_ips',
        'schedule': 86400.0,  # Every day (86400 seconds)
    },
}

# Configure Celery settings
app.conf.update(
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time settings
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Result backend (optional - for storing task results)
    result_backend=None,  # Disabled for this project
    
    # Task routing
    task_routes={
        'ip_tracking.tasks.*': {'queue': 'security'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)
