import logging
import requests
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP, IPGeolocationCache
import dj_database_url

logger = logging.getLogger(__name__)

class IPTrackingMiddleware:
    """
    Middleware to track and log IP addresses, timestamps, and request paths.
    Also blocks requests from IPs in the BlockedIP model.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if IP is blocked before processing
        ip_address = self.get_client_ip(request)
        
        # Check if IP is blocked
        if self.is_ip_blocked(ip_address):
            logger.warning(f"Blocked request from blocked IP: {ip_address}")
            return HttpResponseForbidden("Access denied. Your IP address is blocked.")
        
        # Process request before view
        self.process_request(request)
        
        # Get response from view
        response = self.get_response(request)
        
        # Process response after view
        self.process_response(request, response)
        
        return response
    
    def process_request(self, request):
        """Process the request and log details."""
        # Get client IP address
        ip_address = self.get_client_ip(request)
        path = request.path
        timestamp = timezone.now()
        
        # Get geolocation data
        country, city = self.get_ip_geolocation(ip_address)
        
        # Log to console/logs
        location_info = f" ({city}, {country})" if city and country else ""
        logger.info(f"Request from IP: {ip_address}{location_info}, Path: {path}, Time: {timestamp}")
        
        # Save to database
        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                timestamp=timestamp,
                path=path,
                country=country,
                city=city
            )
        except Exception as e:
            logger.error(f"Failed to save request log: {e}")
    
    def process_response(self, request, response):
        """Process the response (can be used for additional logging if needed)."""
        return response
    
    def get_client_ip(self, request):
        """Extract the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_blocked(self, ip_address):
        """Check if the given IP address is blocked."""
        try:
            return BlockedIP.objects.filter(ip_address=ip_address).exists()
        except Exception as e:
            logger.error(f"Error checking if IP {ip_address} is blocked: {e}")
            return False
    
    def get_ip_geolocation(self, ip_address):
        """Get geolocation data for an IP address, using cache if available."""
        try:
            # Check cache first
            cache_entry = IPGeolocationCache.objects.filter(ip_address=ip_address).first()
            
            if cache_entry and not cache_entry.is_expired(hours=24):
                logger.debug(f"Using cached geolocation data for IP: {ip_address}")
                return cache_entry.country, cache_entry.city
            
            # If not in cache or expired, fetch from API
            country, city = self.fetch_ip_geolocation_from_api(ip_address)
            
            # Update or create cache entry
            if country or city:
                IPGeolocationCache.objects.update_or_create(
                    ip_address=ip_address,
                    defaults={
                        'country': country,
                        'city': city,
                        'cached_at': timezone.now()
                    }
                )
                logger.info(f"Cached geolocation data for IP: {ip_address}")
            
            return country, city
            
        except Exception as e:
            logger.error(f"Error getting geolocation for IP {ip_address}: {e}")
            return None, None
    
    def fetch_ip_geolocation_from_api(self, ip_address):
        """Fetch geolocation data from external API."""
        try:
            # Skip local/private IPs
            if self.is_private_ip(ip_address):
                return None, None
            
            # Use free IP geolocation API (ipapi.co)
            api_url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    country = data.get('country')
                    city = data.get('city')
                    logger.info(f"Fetched geolocation for IP {ip_address}: {city}, {country}")
                    return country, city
                else:
                    logger.warning(f"API returned error for IP {ip_address}: {data.get('message', 'Unknown error')}")
            else:
                logger.warning(f"API request failed for IP {ip_address}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching geolocation for IP {ip_address}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching geolocation for IP {ip_address}: {e}")
        
        return None, None
    
    def is_private_ip(self, ip_address):
        """Check if the IP address is private/local."""
        try:
            # Simple check for common private IP ranges
            if ip_address.startswith(('127.', '10.', '192.168.', '172.')):
                return True
            return False
        except:
            return False
