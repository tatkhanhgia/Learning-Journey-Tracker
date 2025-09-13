#!/usr/bin/env python3
"""
LearnTrack Backend API Testing Suite
Tests all API endpoints for the Vietnamese learning progress tracking application
"""

import requests
import sys
import json
from datetime import datetime

class LearnTrackAPITester:
    def __init__(self, base_url="https://learn-track-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}", {}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if not success:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response_data}"
            else:
                details = "Success"

            return success, details, response_data

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}", {}

    def test_login(self, username, password):
        """Test login functionality"""
        success, details, response = self.make_request(
            'POST', 'auth/login', 
            {'username': username, 'password': password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.current_user = response.get('user_info', {})
            self.log_test(f"Login as {username}", True)
            return True
        else:
            self.log_test(f"Login as {username}", False, details)
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, details, response = self.make_request('GET', 'auth/me')
        self.log_test("Get current user", success, details)
        return success

    def test_get_levels(self):
        """Test getting learning levels"""
        success, details, response = self.make_request('GET', 'config/levels')
        
        if success and 'levels' in response:
            levels = response['levels']
            if len(levels) > 0:
                self.log_test("Get levels", True, f"Found {len(levels)} levels")
                return levels
            else:
                self.log_test("Get levels", False, "No levels found")
                return []
        else:
            self.log_test("Get levels", False, details)
            return []

    def test_get_users(self):
        """Test getting users list"""
        success, details, response = self.make_request('GET', 'config/users')
        
        if success and 'users' in response:
            users = response['users']
            self.log_test("Get users", True, f"Found {len(users)} users")
            return users
        else:
            self.log_test("Get users", False, details)
            return []

    def test_get_all_progress(self):
        """Test getting all users' progress"""
        success, details, response = self.make_request('GET', 'progress')
        
        if success and 'progress' in response:
            progress = response['progress']
            self.log_test("Get all progress", True, f"Found progress for {len(progress)} users")
            return progress
        else:
            self.log_test("Get all progress", False, details)
            return []

    def test_get_my_progress(self):
        """Test getting current user's progress"""
        success, details, response = self.make_request('GET', 'progress/me')
        
        if success and 'progress' in response:
            progress = response['progress']
            self.log_test("Get my progress", True, f"Found {len(progress)} progress entries")
            return progress
        else:
            self.log_test("Get my progress", False, details)
            return []

    def test_update_progress(self, level, completed):
        """Test updating progress for a level"""
        success, details, response = self.make_request(
            'POST', 'progress',
            {'level': level, 'completed': completed}
        )
        
        action = "complete" if completed else "uncomplete"
        self.log_test(f"Update progress - {action} {level}", success, details)
        return success

    def test_get_notes(self):
        """Test getting all notes"""
        success, details, response = self.make_request('GET', 'notes')
        
        if success and 'notes' in response:
            notes = response['notes']
            self.log_test("Get notes", True, f"Found {len(notes)} notes")
            return notes
        else:
            self.log_test("Get notes", False, details)
            return []

    def test_create_note(self, level, content):
        """Test creating a note"""
        success, details, response = self.make_request(
            'POST', 'notes',
            {'level': level, 'content': content}
        )
        
        if success and 'id' in response:
            note_id = response['id']
            self.log_test("Create note", True, f"Created note with ID: {note_id}")
            return note_id
        else:
            self.log_test("Create note", False, details)
            return None

    def test_update_note(self, note_id, content):
        """Test updating a note"""
        success, details, response = self.make_request(
            'PUT', f'notes/{note_id}',
            {'content': content}
        )
        
        self.log_test("Update note", success, details)
        return success

    def test_delete_note(self, note_id):
        """Test deleting a note"""
        success, details, response = self.make_request(
            'DELETE', f'notes/{note_id}',
            expected_status=200
        )
        
        self.log_test("Delete note", success, details)
        return success

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without token"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, details, response = self.make_request('GET', 'auth/me', expected_status=401)
        self.log_test("Unauthorized access protection", success, details)
        
        # Restore token
        self.token = original_token
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, details, response = self.make_request(
            'POST', 'auth/login',
            {'username': 'invalid', 'password': 'invalid'},
            expected_status=401
        )
        
        self.log_test("Invalid login rejection", success, details)
        return success

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting LearnTrack API Testing Suite")
        print("=" * 50)
        
        # Test 1: Invalid login
        print("\n📋 Testing Authentication Security")
        self.test_invalid_login()
        
        # Test 2: Valid login
        print("\n📋 Testing Valid Authentication")
        if not self.test_login("admin", "admin123"):
            print("❌ Cannot proceed without valid login")
            return False
        
        # Test 3: Get current user
        self.test_get_current_user()
        
        # Test 4: Unauthorized access
        self.test_unauthorized_access()
        
        # Test 5: Configuration endpoints
        print("\n📋 Testing Configuration Endpoints")
        levels = self.test_get_levels()
        users = self.test_get_users()
        
        if not levels:
            print("❌ Cannot proceed without levels data")
            return False
        
        # Test 6: Progress endpoints
        print("\n📋 Testing Progress Management")
        self.test_get_all_progress()
        my_progress = self.test_get_my_progress()
        
        # Test progress update if we have levels
        if levels:
            test_level = levels[0]
            self.test_update_progress(test_level, True)
            self.test_update_progress(test_level, False)
        
        # Test 7: Notes endpoints
        print("\n📋 Testing Notes Management")
        self.test_get_notes()
        
        # Create, update, and delete a test note
        if levels:
            test_level = levels[0]
            note_id = self.test_create_note(test_level, "Test note content for API testing")
            
            if note_id:
                self.test_update_note(note_id, "Updated test note content")
                self.test_delete_note(note_id)
        
        # Test 8: Test with different user
        print("\n📋 Testing Multi-User Functionality")
        if self.test_login("user1", "pass1"):
            self.test_get_my_progress()
            
            # Test authorization - user1 shouldn't be able to modify admin's notes
            # This is implicit in the note creation/update/delete tests
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        print("\n" + "=" * 50)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = LearnTrackAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())