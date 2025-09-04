from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
import time
import json


class Command(BaseCommand):
    help = 'Test rate limiting functionality for different user types'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to test with (will create if doesn\'t exist)'
        )
        parser.add_argument(
            '--endpoint',
            type=str,
            default='/api/test-rate-limit/',
            help='Endpoint to test rate limiting on'
        )
    
    def handle(self, *args, **options):
        username = options['user']
        endpoint = options['endpoint']
        
        # Create test user if provided
        if username:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created test user: {username}')
            else:
                self.stdout.write(f'Using existing user: {username}')
        else:
            user = None
            self.stdout.write('Testing with anonymous user')
        
        client = Client()
        
        # Test rate limiting
        self.test_rate_limits(client, endpoint, user)
    
    def test_rate_limits(self, client, endpoint, user):
        """Test rate limiting for the specified endpoint and user."""
        if user:
            # Authenticate user
            client.force_login(user)
            limit = 10  # Authenticated users: 10 requests/minute
            user_type = "authenticated"
        else:
            limit = 5   # Anonymous users: 5 requests/minute
            user_type = "anonymous"
        
        self.stdout.write(f'\nTesting rate limits for {user_type} user:')
        self.stdout.write(f'Endpoint: {endpoint}')
        self.stdout.write(f'Limit: {limit} requests per minute')
        self.stdout.write('-' * 50)
        
        # Make requests up to the limit
        successful_requests = 0
        blocked_requests = 0
        
        for i in range(limit + 2):  # Try to exceed the limit
            response = client.get(endpoint)
            
            if response.status_code == 200:
                successful_requests += 1
                self.stdout.write(f'Request {i+1}: SUCCESS (200)')
            elif response.status_code == 429:  # Too Many Requests
                blocked_requests += 1
                self.stdout.write(f'Request {i+1}: BLOCKED (429) - Rate limit exceeded')
            else:
                self.stdout.write(f'Request {i+1}: UNEXPECTED ({response.status_code})')
            
            # Small delay between requests
            time.sleep(0.1)
        
        # Summary
        self.stdout.write('-' * 50)
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  Successful requests: {successful_requests}')
        self.stdout.write(f'  Blocked requests: {blocked_requests}')
        self.stdout.write(f'  Total requests: {successful_requests + blocked_requests}')
        
        if successful_requests == limit and blocked_requests > 0:
            self.stdout.write(
                self.style.SUCCESS('✓ Rate limiting is working correctly!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Rate limiting may not be working as expected.')
            )
        
        # Test rate limit reset after waiting
        self.stdout.write('\nWaiting 65 seconds for rate limit to reset...')
        time.sleep(65)
        
        # Try one more request
        response = client.get(endpoint)
        if response.status_code == 200:
            self.stdout.write(
                self.style.SUCCESS('✓ Rate limit reset successfully after waiting!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Rate limit may not have reset properly.')
            )
