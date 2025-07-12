#!/usr/bin/env python3
"""
Simple connectivity test to debug API issues
"""

import requests
import json

def test_api_connectivity():
    print("🔍 Testing API Connectivity")
    print("=" * 40)
    
    base_url = "http://localhost:5001"
    
    # Test 1: Basic server connectivity
    print("\n1. Testing basic server connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print("   ✅ Server is responding")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not running or unreachable")
        print("   💡 Make sure to run: ./start_app.sh")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: API base path
    print("\n2. Testing API base path...")
    try:
        response = requests.get(f"{base_url}/api/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ℹ️  API base path returns 404 (expected)")
        else:
            print(f"   Response: {response.text[:100]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: CORS preflight
    print("\n3. Testing CORS preflight...")
    try:
        response = requests.options(
            f"{base_url}/api/auth/register",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
        if 'Access-Control-Allow-Origin' in response.headers:
            print("   ✅ CORS is configured")
        else:
            print("   ⚠️  CORS might not be configured properly")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Direct registration attempt
    print("\n4. Testing registration endpoint...")
    test_user = {
        "email": "connectivity_test@example.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_user,
            headers={
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000'
            },
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 201:
            print("   ✅ Registration endpoint working")
        elif response.status_code == 409:
            print("   ℹ️  User already exists (endpoint working)")
        elif response.status_code == 403:
            print("   ⚠️  403 Forbidden - possible CSRF or authentication issue")
        else:
            print("   ❌ Unexpected response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("📋 Debugging Tips:")
    print("1. Ensure backend is running on http://localhost:5001")
    print("2. Check browser network tab for detailed error info")
    print("3. Verify CORS configuration allows credentials")
    print("4. Check browser console for JavaScript errors")
    print("5. Port 5000 is used by macOS AirPlay - using 5001 instead")
    
    return True

if __name__ == "__main__":
    test_api_connectivity()