import logging
from django.utils import timezone
from .models import RequestLog

logger = logging.getLogger(__name__)

class IPTrackingMiddleware:
    """
    Middleware to track and log IP addresses, timestamps, and request paths.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
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
        
        # Log to console/logs
        logger.info(f"Request from IP: {ip_address}, Path: {path}, Time: {timestamp}")
        
        # Save to database
        try:
            RequestLog.objects.create(
                ip_address=ip_address,
                timestamp=timestamp,
                path=path
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
