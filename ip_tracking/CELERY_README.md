# Celery Tasks for IP Tracking Security

This document describes the Celery-based automated security monitoring system for the IP tracking project.

## Overview

The system uses Celery to automatically monitor IP addresses for suspicious activity and take appropriate actions. Tasks run on a schedule to maintain security without manual intervention.

## Tasks

### 1. Monitor Suspicious IPs (Hourly)
**Task**: `monitor_suspicious_ips`  
**Schedule**: Every hour  
**Purpose**: Analyzes request logs to identify potentially malicious IP addresses

#### Detection Criteria:
- **High Volume**: IPs with >100 requests per hour
- **Sensitive Path Access**: IPs accessing sensitive paths >5 times per hour
- **Failed Login Attempts**: IPs with >10 login attempts per hour
- **Admin Access Attempts**: IPs with >3 admin panel access attempts per hour
- **Brute Force Patterns**: IPs with >200 requests per hour (separate from high volume)

### 2. Cleanup Old Suspicious Flags (Daily)
**Task**: `cleanup_old_suspicious_flags`  
**Schedule**: Every day  
**Purpose**: Deactivates suspicious IP flags older than 7 days

### 3. Auto-Block Severely Suspicious IPs (Daily)
**Task**: `auto_block_suspicious_ips`  
**Schedule**: Every day  
**Purpose**: Automatically blocks IPs flagged for 3+ different suspicious activities

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Redis (Message Broker)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://redis.io/download
```

### 3. Start Redis
```bash
redis-server
```

## Running Celery

### 1. Start Celery Worker
```bash
# Start worker for security tasks
celery -A ip_tracking worker -Q security -l info

# Start worker for all queues
celery -A ip_tracking worker -l info
```

### 2. Start Celery Beat (Scheduler)
```bash
celery -A ip_tracking beat -l info
```

### 3. Start Both Worker and Beat (Development)
```bash
celery -A ip_tracking worker --beat --scheduler django -l info
```

## Configuration

### Celery Settings (settings.py)
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = None
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

### Task Schedule
```python
CELERY_BEAT_SCHEDULE = {
    'monitor-suspicious-ips': {
        'task': 'ip_tracking.tasks.monitor_suspicious_ips',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-suspicious-flags': {
        'task': 'ip_tracking.tasks.cleanup_old_suspicious_flags',
        'schedule': 86400.0,  # Every day
    },
    'auto-block-severely-suspicious-ips': {
        'task': 'ip_tracking.tasks.auto_block_suspicious_ips',
        'schedule': 86400.0,  # Every day
    },
}
```

## Management Commands

### Manual Task Execution
```bash
# Run all tasks
python manage.py monitor_suspicious_ips

# Run specific task
python manage.py monitor_suspicious_ips --task monitor

# Dry run (show what would be done)
python manage.py monitor_suspicious_ips --dry-run
```

### Available Tasks
- `monitor`: Run suspicious IP monitoring
- `cleanup`: Clean up old suspicious flags
- `auto-block`: Auto-block severely suspicious IPs
- `all`: Run all tasks (default)

## Monitoring and Logging

### Task Logs
All tasks log their activities with appropriate log levels:
- `INFO`: Task start/completion, normal operations
- `WARNING`: Suspicious IPs detected
- `ERROR`: Task failures, system errors

### Log Format
```
[timestamp] INFO: Starting suspicious IP monitoring task
[timestamp] INFO: Checking for high volume IPs...
[timestamp] WARNING: Flagged IP 192.168.1.100 for high volume: 150 requests
[timestamp] INFO: Suspicious IP monitoring completed. Flagged 3 IPs
```

## Suspicious IP Model

### Fields
- `ip_address`: The flagged IP address
- `reason`: Type of suspicious activity
- `details`: Additional context about the activity
- `request_count`: Number of requests that triggered the flag
- `first_seen`: When the IP was first flagged
- `last_seen`: When the IP was last flagged
- `is_active`: Whether the flag is still active

### Suspicious Reasons
- `high_volume`: Excessive request volume
- `sensitive_paths`: Accessing sensitive endpoints
- `failed_logins`: Multiple failed authentication attempts
- `admin_access`: Admin panel access attempts
- `brute_force`: Automated attack patterns

## Production Considerations

### 1. Redis Persistence
```bash
# Enable Redis persistence
redis-cli config set save "900 1 300 10 60 10000"
```

### 2. Celery Worker Scaling
```bash
# Start multiple workers
celery -A ip_tracking worker -Q security -c 4 -l info
```

### 3. Monitoring
- Use Flower for Celery monitoring: `pip install flower`
- Start Flower: `celery -A ip_tracking flower`
- Access at: `http://localhost:5555`

### 4. Error Handling
- Tasks include comprehensive error handling
- Failed tasks are logged with full error details
- System continues operating even if individual tasks fail

## Troubleshooting

### Common Issues

#### 1. Redis Connection Error
```
Error: Connection refused to Redis
Solution: Ensure Redis server is running
```

#### 2. Task Not Executing
```
Error: Tasks not running on schedule
Solution: Check Celery Beat is running
```

#### 3. Worker Not Processing Tasks
```
Error: Worker not processing tasks
Solution: Check worker is running and connected to correct queue
```

### Debug Mode
```bash
# Enable debug logging
celery -A ip_tracking worker -l debug

# Check task status
celery -A ip_tracking inspect active
celery -A ip_tracking inspect scheduled
```

## Security Features

### 1. Automatic Detection
- Real-time monitoring of request patterns
- Configurable thresholds for different types of activity
- Multiple detection methods for comprehensive coverage

### 2. Progressive Response
- Flag suspicious IPs for monitoring
- Auto-block IPs with severe suspicious activity
- Maintain audit trail of all actions

### 3. Configurable Thresholds
- High volume: >100 requests/hour
- Sensitive paths: >5 attempts/hour
- Failed logins: >10 attempts/hour
- Admin access: >3 attempts/hour
- Brute force: >200 requests/hour

This automated system provides continuous security monitoring while maintaining detailed logs and audit trails for all security-related actions.
