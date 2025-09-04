from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib import messages
import json
import logging

logger = logging.getLogger(__name__)


@sensitive_post_parameters('password')
@never_cache
@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    Sensitive login view that requires rate limiting.
    This view handles user authentication and should be protected against brute force attacks.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required'
            }, status=400)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"Successful login for user: {username} from IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username
            })
        else:
            logger.warning(f"Failed login attempt for username: {username} from IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


@login_required
def dashboard_view(request):
    """
    Protected dashboard view that requires authentication.
    """
    return JsonResponse({
        'message': 'Welcome to the dashboard',
        'user': request.user.username,
        'is_authenticated': request.user.is_authenticated
    })


@login_required
def profile_view(request):
    """
    User profile view that requires authentication.
    """
    return JsonResponse({
        'message': 'User profile',
        'username': request.user.username,
        'email': request.user.email,
        'date_joined': request.user.date_joined.isoformat()
    })


def health_check(request):
    """
    Public health check endpoint (no rate limiting needed).
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'Service is running'
    })


class RateLimitTestView(View):
    """
    Test view to demonstrate rate limiting functionality.
    """
    
    def get(self, request):
        """GET method for testing rate limits."""
        return JsonResponse({
            'message': 'Rate limit test - GET',
            'method': 'GET',
            'timestamp': request.timestamp if hasattr(request, 'timestamp') else None
        })
    
    def post(self, request):
        """POST method for testing rate limits."""
        return JsonResponse({
            'message': 'Rate limit test - POST',
            'method': 'POST',
            'timestamp': request.timestamp if hasattr(request, 'timestamp') else None
        })
