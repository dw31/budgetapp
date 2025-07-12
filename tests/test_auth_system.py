#!/usr/bin/env python3
"""
Test script for the authentication system
"""

import requests
import json
import os

def test_auth_system():
    base_url = "http://localhost:5000/api"
    
    print("🧪 Banking App - Authentication System Test")
    print("=" * 60)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    session = requests.Session()
    
    try:
        # Test 1: Register new user
        print("\n1. Testing user registration...")
        response = session.post(
            f"{base_url}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print("✅ User registration successful")
        elif response.status_code == 409:
            print("ℹ️  User already exists (expected if run multiple times)")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
        
        # Test 2: Login
        print("\n2. Testing user login...")
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        response = session.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ User login successful")
            user_data = response.json()
            print(f"   User: {user_data['user']['first_name']} {user_data['user']['last_name']}")
            print(f"   Email: {user_data['user']['email']}")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
        
        # Test 3: Get current user
        print("\n3. Testing get current user...")
        response = session.get(f"{base_url}/auth/me")
        
        if response.status_code == 200:
            print("✅ Get current user successful")
            user = response.json()['user']
            print(f"   User ID: {user['id']}")
            print(f"   Created: {user['created_at']}")
        else:
            print(f"❌ Get current user failed: {response.status_code} - {response.text}")
        
        # Test 4: Update profile
        print("\n4. Testing profile update...")
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = session.put(
            f"{base_url}/auth/profile",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Profile update successful")
            updated_user = response.json()['user']
            print(f"   Updated name: {updated_user['first_name']} {updated_user['last_name']}")
        else:
            print(f"❌ Profile update failed: {response.status_code} - {response.text}")
        
        # Test 5: Change password
        print("\n5. Testing password change...")
        password_data = {
            "current_password": test_user["password"],
            "new_password": "newpass123"
        }
        
        response = session.post(
            f"{base_url}/auth/change-password",
            json=password_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Password change successful")
        else:
            print(f"❌ Password change failed: {response.status_code} - {response.text}")
        
        # Test 6: Logout
        print("\n6. Testing logout...")
        response = session.post(f"{base_url}/auth/logout")
        
        if response.status_code == 200:
            print("✅ Logout successful")
        else:
            print(f"❌ Logout failed: {response.status_code} - {response.text}")
        
        # Test 7: Verify session is cleared
        print("\n7. Testing session cleared...")
        response = session.get(f"{base_url}/auth/me")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Session properly cleared")
        else:
            print(f"❌ Session not cleared: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("🎉 Authentication system test completed!")
        print("\n✨ Available Features:")
        print("   🔐 User Registration and Login")
        print("   👤 User Profile Management")
        print("   📷 Avatar Upload Support")
        print("   🔒 Password Change")
        print("   🚪 Secure Logout")
        print("   🛡️  Session-based Authentication")
        print("\n📋 Frontend Pages:")
        print("   • /login - User login page")
        print("   • /register - User registration page")
        print("   • /profile - User profile management")
        print("   • Protected routes with authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_auth_system()
    exit(0 if success else 1)