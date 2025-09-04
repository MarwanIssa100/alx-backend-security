"""
URL configuration for ip_tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication endpoints (rate limited)
    path('api/login/', views.login_view, name='login'),
    
    # Protected endpoints (rate limited for authenticated users)
    path('api/dashboard/', views.dashboard_view, name='dashboard'),
    path('api/profile/', views.profile_view, name='profile'),
    
    # Public endpoints (no rate limiting)
    path('health/', views.health_check, name='health_check'),
    
    # Rate limit test endpoints
    path('api/test-rate-limit/', views.RateLimitTestView.as_view(), name='test_rate_limit'),
]
