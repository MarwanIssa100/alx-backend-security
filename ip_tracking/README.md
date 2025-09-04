# IP Tracking Project

A Django project that tracks IP addresses, blocks malicious IPs, and provides geolocation information for requests.

## Features

- **IP Request Logging**: Automatically logs all incoming requests with IP address, timestamp, path, and geolocation data
- **IP Blocking**: Block specific IP addresses from accessing the site
- **Geolocation**: Automatically detects country and city for each IP address
- **Caching**: 24-hour cache for geolocation data to minimize API calls
- **Rate Limiting**: Configurable rate limits (10 req/min for authenticated users, 5 req/min for anonymous users)
- **Management Commands**: Easy-to-use commands for managing blocked IPs, cache, and testing rate limits

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Usage

### Block an IP Address
```bash
python manage.py block_ip 192.168.1.100 --reason "Suspicious activity"
```

### Unblock an IP Address
```bash
python manage.py unblock_ip 192.168.1.100
```

### Clear Expired Cache
```bash
# Clear cache entries older than 24 hours (default)
python manage.py clear_expired_cache

# Clear cache entries older than 48 hours
python manage.py clear_expired_cache --hours 48

# Preview what would be deleted (dry run)
python manage.py clear_expired_cache --dry-run
```

### Test Rate Limits
```bash
# Test rate limiting for anonymous users
python manage.py test_rate_limits

# Test rate limiting for authenticated users
python manage.py test_rate_limits --user testuser

# Test rate limiting on specific endpoint
python manage.py test_rate_limits --endpoint /api/login/
```

## Models

### RequestLog
Stores information about each request:
- `ip_address`: Client IP address
- `timestamp`: Request timestamp
- `path`: Requested URL path
- `country`: Country where IP is located
- `city`: City where IP is located

### BlockedIP
Stores blocked IP addresses:
- `ip_address`: Blocked IP address
- `created_at`: When the IP was blocked
- `reason`: Optional reason for blocking

### IPGeolocationCache
Caches geolocation data to avoid repeated API calls:
- `ip_address`: IP address
- `country`: Cached country data
- `city`: Cached city data
- `cached_at`: When data was cached

## Middleware

### IPTrackingMiddleware
Automatically:
1. Checks if the requesting IP is blocked
2. Logs request details to the database
3. Fetches and caches geolocation data
4. Returns 403 Forbidden for blocked IPs

### RateLimitMiddleware
Applies rate limiting:
1. **Authenticated users**: 10 requests per minute
2. **Anonymous users**: 5 requests per minute
3. **Sliding window**: 60-second window for rate calculation
4. **Cache-based**: Uses Django's cache framework for tracking
5. **Configurable**: Limits and paths can be configured in settings

## Geolocation API

Uses the free [IP-API](http://ip-api.com/) service for geolocation data. The service:
- Provides country and city information
- Has a rate limit of 1000 requests per minute
- Automatically skips private/local IP addresses
- Caches results for 24 hours

## Configuration

### Rate Limiting
Rate limiting is configured in `settings.py`:

```python
RATE_LIMIT_CONFIG = {
    'AUTHENTICATED_USERS': {
        'REQUESTS_PER_MINUTE': 10,
        'WINDOW_SIZE': 60,  # seconds
    },
    'ANONYMOUS_USERS': {
        'REQUESTS_PER_MINUTE': 5,
        'WINDOW_SIZE': 60,  # seconds
    },
    'SKIP_PATHS': [
        '/health/',
        '/static/',
        '/media/',
        '/admin/jsi18n/',
    ],
}
```

### Cache Configuration
Rate limiting uses Django's cache framework:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}
```

The middleware is automatically registered in `settings.py`. No additional configuration is required.

## Notes

- Private IP addresses (127.x.x.x, 10.x.x.x, 192.168.x.x, 172.x.x.x) are automatically skipped for geolocation
- Cache entries expire after 24 hours and can be manually cleared
- All geolocation API calls are logged for monitoring
- Failed geolocation requests don't prevent request logging
