#!/usr/bin/env python3
"""
Simple test script to demonstrate rate limiting functionality.
This script can be used to test the rate limiting from outside Django.
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your Django server URL
LOGIN_ENDPOINT = f"{BASE_URL}/api/login/"
TEST_ENDPOINT = f"{BASE_URL}/api/test-rate-limit/"

def test_anonymous_rate_limit():
    """Test rate limiting for anonymous users (limit: 5 requests/minute)."""
    print("Testing Anonymous User Rate Limiting (5 requests/minute)")
    print("=" * 60)
    
    successful = 0
    blocked = 0
    
    for i in range(7):  # Try to exceed the 5 request limit
        try:
            response = requests.get(TEST_ENDPOINT, timeout=5)
            
            if response.status_code == 200:
                successful += 1
                print(f"Request {i+1}: SUCCESS (200)")
            elif response.status_code == 429:
                blocked += 1
                print(f"Request {i+1}: BLOCKED (429) - Rate limit exceeded")
            else:
                print(f"Request {i+1}: UNEXPECTED ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\nSummary: {successful} successful, {blocked} blocked")
    return successful, blocked

def test_authenticated_rate_limit(username, password):
    """Test rate limiting for authenticated users (limit: 10 requests/minute)."""
    print(f"\nTesting Authenticated User Rate Limiting (10 requests/minute)")
    print(f"Username: {username}")
    print("=" * 60)
    
    # First, try to login
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        login_response = requests.post(LOGIN_ENDPOINT, json=login_data, timeout=5)
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            # Get session cookies
            cookies = login_response.cookies
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"✗ Login error: {e}")
        return
    
    # Test rate limiting with authenticated session
    successful = 0
    blocked = 0
    
    for i in range(12):  # Try to exceed the 10 request limit
        try:
            response = requests.get(TEST_ENDPOINT, cookies=cookies, timeout=5)
            
            if response.status_code == 200:
                successful += 1
                print(f"Request {i+1}: SUCCESS (200)")
            elif response.status_code == 429:
                blocked += 1
                print(f"Request {i+1}: BLOCKED (429) - Rate limit exceeded")
            else:
                print(f"Request {i+1}: UNEXPECTED ({response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\nSummary: {successful} successful, {blocked} blocked")
    return successful, blocked

def main():
    """Main test function."""
    print("Django Rate Limiting Test Script")
    print("=" * 40)
    
    # Test anonymous rate limiting
    anon_success, anon_blocked = test_anonymous_rate_limit()
    
    # Test authenticated rate limiting (if credentials provided)
    username = input("\nEnter username for authenticated test (or press Enter to skip): ").strip()
    if username:
        password = input("Enter password: ").strip()
        if password:
            auth_success, auth_blocked = test_authenticated_rate_limit(username, password)
        else:
            print("No password provided, skipping authenticated test")
    else:
        print("No username provided, skipping authenticated test")
    
    # Overall summary
    print("\n" + "=" * 40)
    print("OVERALL SUMMARY")
    print("=" * 40)
    print(f"Anonymous users: {anon_success} successful, {anon_blocked} blocked")
    
    if 'auth_success' in locals():
        print(f"Authenticated users: {auth_success} successful, {auth_blocked} blocked")
    
    print("\nRate limiting is working correctly if:")
    print("- Anonymous users were blocked after 5 requests")
    print("- Authenticated users were blocked after 10 requests")
    print("- Health endpoint (/health/) should not be rate limited")

if __name__ == "__main__":
    main()
