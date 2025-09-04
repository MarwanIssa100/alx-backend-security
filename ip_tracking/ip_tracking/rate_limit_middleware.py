import time
import logging
from django.http import HttpResponseTooManyRequests
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware that applies different limits for authenticated vs anonymous users.
    - Authenticated users: 10 requests per minute
    - Anonymous users: 5 requests per minute
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Rate limits in requests per minute
        self.authenticated_limit = 10
        self.anonymous_limit = 5
        self.window_size = 60  # 60 seconds = 1 minute
    
    def process_request(self, request):
        """Process the request and apply rate limiting."""
        # Skip rate limiting for certain paths if needed
        if self.should_skip_rate_limit(request.path):
            return None
        
        # Get client IP address
        ip_address = self.get_client_ip(request)
        
        # Determine if user is authenticated
        is_authenticated = request.user.is_authenticated
        
        # Apply appropriate rate limit
        if is_authenticated:
            limit = self.authenticated_limit
            user_id = request.user.id
            cache_key = f"rate_limit_auth_{user_id}_{ip_address}"
        else:
            limit = self.anonymous_limit
            user_id = None
            cache_key = f"rate_limit_anon_{ip_address}"
        
        # Check rate limit
        if not self.check_rate_limit(cache_key, limit):
            logger.warning(
                f"Rate limit exceeded for {'authenticated' if is_authenticated else 'anonymous'} "
                f"user from IP: {ip_address}"
            )
            return HttpResponseTooManyRequests(
                f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                content_type="text/plain"
            )
        
        return None
    
    def should_skip_rate_limit(self, path):
        """Determine if rate limiting should be skipped for this path."""
        # Skip rate limiting for health checks and static files
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/admin/jsi18n/',
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def get_client_ip(self, request):
        """Extract the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, cache_key, limit):
        """
        Check if the request is within the rate limit.
        Returns True if the request is allowed, False if rate limit exceeded.
        """
        try:
            # Get current timestamp
            now = int(time.time())
            
            # Get existing requests from cache
            requests_data = cache.get(cache_key, [])
            
            # Remove requests older than the window
            window_start = now - self.window_size
            requests_data = [req_time for req_time in requests_data if req_time > window_start]
            
            # Check if adding this request would exceed the limit
            if len(requests_data) >= limit:
                return False
            
            # Add current request
            requests_data.append(now)
            
            # Store updated requests in cache
            # Cache for slightly longer than window size to ensure cleanup
            cache.set(cache_key, requests_data, self.window_size + 10)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for key {cache_key}: {e}")
            # In case of error, allow the request (fail open)
            return True
    
    def process_response(self, request, response):
        """Process the response (can be used for additional logging if needed)."""
        return response
