#!/usr/bin/env python3
"""
LearnTrack Backend API Testing Suite - Hierarchical Learning Structure
Tests all API endpoints for the Vietnamese learning progress tracking application
with new 3-tier hierarchy: Resources → Modules → Sessions
"""

import requests
import sys
import json
from datetime import datetime

class LearnTrackHierarchicalAPITester:
    def __init__(self, base_url="https://learn-track-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.learning_structure = None

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

    def test_get_learning_structure(self):
        """Test getting complete learning structure"""
        success, details, response = self.make_request('GET', 'structure')
        
        if success and 'resources' in response:
            self.learning_structure = response
            resources = response['resources']
            total_modules = sum(len(r.get('modules', [])) for r in resources)
            total_sessions = sum(len(m.get('sessions', [])) for r in resources for m in r.get('modules', []))
            
            self.log_test("Get learning structure", True, 
                         f"Found {len(resources)} resources, {total_modules} modules, {total_sessions} sessions")
            return response
        else:
            self.log_test("Get learning structure", False, details)
            return None

    def test_get_resources(self):
        """Test getting all resources"""
        success, details, response = self.make_request('GET', 'structure/resources')
        
        if success and 'resources' in response:
            resources = response['resources']
            self.log_test("Get resources", True, f"Found {len(resources)} resources")
            return resources
        else:
            self.log_test("Get resources", False, details)
            return []

    def test_get_modules(self, resource_name):
        """Test getting modules for a specific resource"""
        success, details, response = self.make_request('GET', f'structure/resources/{resource_name}/modules')
        
        if success and 'modules' in response:
            modules = response['modules']
            self.log_test(f"Get modules for {resource_name}", True, f"Found {len(modules)} modules")
            return modules
        else:
            self.log_test(f"Get modules for {resource_name}", False, details)
            return []

    def test_get_sessions(self, resource_name, module_name):
        """Test getting sessions for a specific module"""
        success, details, response = self.make_request('GET', f'structure/resources/{resource_name}/modules/{module_name}/sessions')
        
        if success and 'sessions' in response:
            sessions = response['sessions']
            session_types = [s.get('type', 'unknown') for s in sessions]
            self.log_test(f"Get sessions for {resource_name}/{module_name}", True, 
                         f"Found {len(sessions)} sessions (types: {', '.join(set(session_types))})")
            return sessions
        else:
            self.log_test(f"Get sessions for {resource_name}/{module_name}", False, details)
            return []

    def test_invalid_structure_endpoints(self):
        """Test structure endpoints with invalid parameters"""
        # Test invalid resource
        success, details, response = self.make_request('GET', 'structure/resources/InvalidResource/modules', expected_status=404)
        self.log_test("Invalid resource rejection", success, details)
        
        # Test invalid module
        success, details, response = self.make_request('GET', 'structure/resources/Youtube/modules/InvalidModule/sessions', expected_status=404)
        self.log_test("Invalid module rejection", success, details)

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
        """Test getting all users' progress in hierarchical format"""
        success, details, response = self.make_request('GET', 'progress')
        
        if success and 'progress' in response:
            progress = response['progress']
            # Validate hierarchical structure
            if progress and len(progress) > 0:
                user_progress = progress[0]
                if 'resources' in user_progress:
                    self.log_test("Get all progress (hierarchical)", True, 
                                 f"Found hierarchical progress for {len(progress)} users")
                    return progress
                else:
                    self.log_test("Get all progress (hierarchical)", False, "Progress not in hierarchical format")
                    return []
            else:
                self.log_test("Get all progress (hierarchical)", True, "No progress data yet")
                return progress
        else:
            self.log_test("Get all progress (hierarchical)", False, details)
            return []

    def test_get_my_progress(self):
        """Test getting current user's progress in hierarchical format"""
        success, details, response = self.make_request('GET', 'progress/me')
        
        if success and 'progress' in response:
            progress = response['progress']
            # Validate hierarchical structure
            if progress and len(progress) > 0:
                resource_progress = progress[0]
                if 'modules' in resource_progress:
                    self.log_test("Get my progress (hierarchical)", True, 
                                 f"Found hierarchical progress with {len(progress)} resources")
                    return progress
                else:
                    self.log_test("Get my progress (hierarchical)", False, "Progress not in hierarchical format")
                    return []
            else:
                self.log_test("Get my progress (hierarchical)", True, "No progress data yet")
                return progress
        else:
            self.log_test("Get my progress (hierarchical)", False, details)
            return []

    def test_update_progress(self, resource, module, session, completed):
        """Test updating progress for hierarchical structure"""
        success, details, response = self.make_request(
            'POST', 'progress',
            {
                'resource': resource,
                'module': module, 
                'session': session,
                'completed': completed
            }
        )
        
        action = "complete" if completed else "uncomplete"
        self.log_test(f"Update progress - {action} {resource}/{module}/{session}", success, details)
        return success

    def test_invalid_progress_update(self):
        """Test updating progress with invalid resource/module/session"""
        success, details, response = self.make_request(
            'POST', 'progress',
            {
                'resource': 'InvalidResource',
                'module': 'InvalidModule',
                'session': 'InvalidSession',
                'completed': True
            },
            expected_status=400
        )
        
        self.log_test("Invalid progress update rejection", success, details)
        return success

    def test_get_notes(self):
        """Test getting all notes with hierarchical context"""
        success, details, response = self.make_request('GET', 'notes')
        
        if success and 'notes' in response:
            notes = response['notes']
            # Validate hierarchical fields
            if notes and len(notes) > 0:
                note = notes[0]
                has_hierarchy = all(field in note for field in ['resource', 'module', 'session'])
                if has_hierarchy:
                    self.log_test("Get notes (hierarchical)", True, f"Found {len(notes)} notes with hierarchical context")
                else:
                    self.log_test("Get notes (hierarchical)", False, "Notes missing hierarchical context")
                return notes
            else:
                self.log_test("Get notes (hierarchical)", True, "No notes found")
                return notes
        else:
            self.log_test("Get notes (hierarchical)", False, details)
            return []

    def test_create_note(self, resource, module, session, content):
        """Test creating a note with hierarchical context"""
        success, details, response = self.make_request(
            'POST', 'notes',
            {
                'resource': resource,
                'module': module,
                'session': session,
                'content': content
            }
        )
        
        if success and 'id' in response:
            note_id = response['id']
            self.log_test(f"Create note for {resource}/{module}/{session}", True, f"Created note with ID: {note_id}")
            return note_id
        else:
            self.log_test(f"Create note for {resource}/{module}/{session}", False, details)
            return None

    def test_invalid_note_creation(self):
        """Test creating note with invalid resource/module/session"""
        success, details, response = self.make_request(
            'POST', 'notes',
            {
                'resource': 'InvalidResource',
                'module': 'InvalidModule',
                'session': 'InvalidSession',
                'content': 'Test note'
            },
            expected_status=400
        )
        
        self.log_test("Invalid note creation rejection", success, details)
        return success

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
        print("🚀 Starting LearnTrack Hierarchical API Testing Suite")
        print("=" * 60)
        
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
        
        # Test 5: Hierarchical Structure endpoints
        print("\n📋 Testing Hierarchical Learning Structure")
        structure = self.test_get_learning_structure()
        if not structure:
            print("❌ Cannot proceed without learning structure")
            return False
        
        resources = self.test_get_resources()
        
        # Test structure navigation - use Page resource for better URL compatibility
        if resources and len(resources) > 0:
            # Find Page resource for testing (has English module names)
            test_resource = "Page"
            for r in resources:
                if r['name'] == 'Page':
                    test_resource = r['name']
                    break
            
            modules = self.test_get_modules(test_resource)
            
            if modules and len(modules) > 0:
                test_module = modules[0]['name']  # Should be "Module 1: React Basics"
                sessions = self.test_get_sessions(test_resource, test_module)
        
        # Test invalid structure endpoints
        self.test_invalid_structure_endpoints()
        
        # Test 6: Configuration endpoints
        print("\n📋 Testing Configuration Endpoints")
        users = self.test_get_users()
        
        # Test 7: Hierarchical Progress endpoints
        print("\n📋 Testing Hierarchical Progress Management")
        self.test_get_all_progress()
        my_progress = self.test_get_my_progress()
        
        # Test progress update with hierarchical structure - use Page resource
        if structure and structure['resources']:
            # Find Page resource for testing
            page_resource = None
            for resource in structure['resources']:
                if resource['name'] == 'Page':
                    page_resource = resource
                    break
            
            if page_resource and page_resource['modules']:
                test_resource = page_resource['name']
                test_module = page_resource['modules'][0]['name']
                if page_resource['modules'][0]['sessions']:
                    test_session = page_resource['modules'][0]['sessions'][0]['name']
                    
                    self.test_update_progress(test_resource, test_module, test_session, True)
                    self.test_update_progress(test_resource, test_module, test_session, False)
        
        # Test invalid progress update
        self.test_invalid_progress_update()
        
        # Test 8: Hierarchical Notes endpoints
        print("\n📋 Testing Hierarchical Notes Management")
        self.test_get_notes()
        
        # Create, update, and delete a test note with hierarchical context
        if structure and structure['resources']:
            test_resource = structure['resources'][0]['name']
            if structure['resources'][0]['modules']:
                test_module = structure['resources'][0]['modules'][0]['name']
                if structure['resources'][0]['modules'][0]['sessions']:
                    test_session = structure['resources'][0]['modules'][0]['sessions'][0]['name']
                    
                    note_id = self.test_create_note(test_resource, test_module, test_session, 
                                                   "Test note for hierarchical learning structure")
                    
                    if note_id:
                        self.test_update_note(note_id, "Updated test note for hierarchical structure")
                        self.test_delete_note(note_id)
        
        # Test invalid note creation
        self.test_invalid_note_creation()
        
        # Test 9: Test with different user
        print("\n📋 Testing Multi-User Functionality")
        if self.test_login("user1", "pass1"):
            self.test_get_my_progress()
            
            # Test creating note as different user
            if structure and structure['resources']:
                test_resource = structure['resources'][1]['name'] if len(structure['resources']) > 1 else structure['resources'][0]['name']
                if structure['resources'][0]['modules']:
                    test_module = structure['resources'][0]['modules'][0]['name']
                    if structure['resources'][0]['modules'][0]['sessions']:
                        test_session = structure['resources'][0]['modules'][0]['sessions'][0]['name']
                        
                        user1_note_id = self.test_create_note(test_resource, test_module, test_session, 
                                                             "Note from user1 in hierarchical system")
                        if user1_note_id:
                            self.test_delete_note(user1_note_id)
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 HIERARCHICAL LEARNING STRUCTURE TEST SUMMARY")
        print("=" * 60)
        
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
        
        print("\n" + "=" * 60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = LearnTrackHierarchicalAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        all_passed = tester.print_summary()
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())