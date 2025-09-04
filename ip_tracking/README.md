# IP Tracking Project

A Django project that tracks IP addresses, blocks malicious IPs, and provides geolocation information for requests.

## Features

- **IP Request Logging**: Automatically logs all incoming requests with IP address, timestamp, path, and geolocation data
- **IP Blocking**: Block specific IP addresses from accessing the site
- **Geolocation**: Automatically detects country and city for each IP address
- **Caching**: 24-hour cache for geolocation data to minimize API calls
- **Management Commands**: Easy-to-use commands for managing blocked IPs and cache

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

The `IPTrackingMiddleware` automatically:
1. Checks if the requesting IP is blocked
2. Logs request details to the database
3. Fetches and caches geolocation data
4. Returns 403 Forbidden for blocked IPs

## Geolocation API

Uses the free [IP-API](http://ip-api.com/) service for geolocation data. The service:
- Provides country and city information
- Has a rate limit of 1000 requests per minute
- Automatically skips private/local IP addresses
- Caches results for 24 hours

## Configuration

The middleware is automatically registered in `settings.py`. No additional configuration is required.

## Notes

- Private IP addresses (127.x.x.x, 10.x.x.x, 192.168.x.x, 172.x.x.x) are automatically skipped for geolocation
- Cache entries expire after 24 hours and can be manually cleared
- All geolocation API calls are logged for monitoring
- Failed geolocation requests don't prevent request logging
