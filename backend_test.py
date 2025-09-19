#!/usr/bin/env python3
"""
LearnTrack Backend API Testing Suite - Hierarchical Learning Structure
Tests all API endpoints for the Vietnamese learning progress tracking application
with new 3-tier hierarchy: Resources → Modules → Sessions
"""

import requests
import sys
import json
import io
from datetime import datetime

class LearnTrackHierarchicalAPITester:
    def __init__(self, base_url="https://api-gtk.taileb239e.ts.net"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.current_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.learning_structure = None
        self.created_shares = []  # Track created shares for cleanup

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
        
        success, details, response = self.make_request('GET', 'auth/me', expected_status=403)
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

    # Sharing System Tests
    def test_get_shares_empty(self):
        """Test getting shares when none exist"""
        success, details, response = self.make_request('GET', 'shares')
        
        if success and 'items' in response:
            shares = response['items']
            total = response.get('total', 0)
            self.log_test("Get shares (empty)", True, f"Found {len(shares)} shares, total: {total}")
            return response
        else:
            self.log_test("Get shares (empty)", False, details)
            return None

    def test_create_url_share(self, title, description, url):
        """Test creating a URL share"""
        success, details, response = self.make_request(
            'POST', 'shares',
            {
                'title': title,
                'description': description,
                'type': 'url',
                'content': url
            }
        )
        
        if success and 'id' in response:
            share_id = response['id']
            self.created_shares.append(share_id)
            self.log_test(f"Create URL share: {title}", True, f"Created share with ID: {share_id}")
            return share_id
        else:
            self.log_test(f"Create URL share: {title}", False, details)
            return None

    def test_create_invalid_url_share(self):
        """Test creating URL share with invalid URL"""
        success, details, response = self.make_request(
            'POST', 'shares',
            {
                'title': 'Invalid URL Test',
                'description': 'Testing invalid URL',
                'type': 'url',
                'content': 'not-a-valid-url'
            },
            expected_status=400
        )
        
        self.log_test("Invalid URL share rejection", success, details)
        return success

    def test_create_file_share_via_url_endpoint(self):
        """Test creating file share via URL endpoint (should fail)"""
        success, details, response = self.make_request(
            'POST', 'shares',
            {
                'title': 'File Test',
                'description': 'Testing file via URL endpoint',
                'type': 'file',
                'content': 'test.pdf'
            },
            expected_status=400
        )
        
        self.log_test("File share via URL endpoint rejection", success, details)
        return success

    def test_upload_file_share(self, title, description, filename, content, content_type):
        """Test uploading a file share"""
        url = f"{self.api_url}/shares/upload"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        # Create multipart form data
        files = {
            'file': (filename, io.BytesIO(content.encode() if isinstance(content, str) else content), content_type)
        }
        data = {
            'title': title,
            'description': description
        }

        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if success and 'id' in response_data:
                share_id = response_data['id']
                self.created_shares.append(share_id)
                self.log_test(f"Upload file share: {title}", True, f"Uploaded file with ID: {share_id}")
                return share_id
            else:
                details = f"Status: {response.status_code}, Response: {response_data}"
                self.log_test(f"Upload file share: {title}", False, details)
                return None

        except requests.exceptions.RequestException as e:
            self.log_test(f"Upload file share: {title}", False, f"Request failed: {str(e)}")
            return None

    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        url = f"{self.api_url}/shares/upload"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        # Create multipart form data with invalid file type
        files = {
            'file': ('test.exe', io.BytesIO(b'fake executable content'), 'application/x-executable')
        }
        data = {
            'title': 'Invalid File Type Test',
            'description': 'Testing invalid file type'
        }

        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=10)
            success = response.status_code == 400
            
            self.log_test("Invalid file type rejection", success, f"Status: {response.status_code}")
            return success

        except requests.exceptions.RequestException as e:
            self.log_test("Invalid file type rejection", False, f"Request failed: {str(e)}")
            return False

    def test_upload_large_file(self):
        """Test uploading file exceeding size limit"""
        url = f"{self.api_url}/shares/upload"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        # Create large file content (11MB)
        large_content = b'x' * (11 * 1024 * 1024)
        files = {
            'file': ('large_file.txt', io.BytesIO(large_content), 'text/plain')
        }
        data = {
            'title': 'Large File Test',
            'description': 'Testing file size limit'
        }

        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            success = response.status_code == 400
            
            self.log_test("Large file rejection", success, f"Status: {response.status_code}")
            return success

        except requests.exceptions.RequestException as e:
            self.log_test("Large file rejection", False, f"Request failed: {str(e)}")
            return False

    def test_get_shares_with_pagination(self, page=1, limit=5):
        """Test getting shares with pagination"""
        success, details, response = self.make_request('GET', f'shares?page={page}&limit={limit}')
        
        if success and 'items' in response:
            shares = response['items']
            total = response.get('total', 0)
            current_page = response.get('page', 1)
            total_pages = response.get('total_pages', 1)
            
            self.log_test(f"Get shares with pagination (page {page}, limit {limit})", True, 
                         f"Found {len(shares)} shares, total: {total}, page: {current_page}/{total_pages}")
            return response
        else:
            self.log_test(f"Get shares with pagination (page {page}, limit {limit})", False, details)
            return None

    def test_search_shares(self, search_term):
        """Test searching shares"""
        success, details, response = self.make_request('GET', f'shares?search={search_term}')
        
        if success and 'items' in response:
            shares = response['items']
            total = response.get('total', 0)
            self.log_test(f"Search shares: '{search_term}'", True, f"Found {len(shares)} matching shares")
            return response
        else:
            self.log_test(f"Search shares: '{search_term}'", False, details)
            return None

    def test_filter_shares_by_type(self, type_filter):
        """Test filtering shares by type"""
        success, details, response = self.make_request('GET', f'shares?type_filter={type_filter}')
        
        if success and 'items' in response:
            shares = response['items']
            total = response.get('total', 0)
            # Verify all returned shares match the filter
            if shares:
                types = [share.get('type') for share in shares]
                all_match = all(t == type_filter for t in types) if type_filter != 'all' else True
                if all_match:
                    self.log_test(f"Filter shares by type: {type_filter}", True, f"Found {len(shares)} {type_filter} shares")
                else:
                    self.log_test(f"Filter shares by type: {type_filter}", False, f"Filter not working correctly: {types}")
            else:
                self.log_test(f"Filter shares by type: {type_filter}", True, f"No {type_filter} shares found")
            return response
        else:
            self.log_test(f"Filter shares by type: {type_filter}", False, details)
            return None

    def test_get_file(self, filename):
        """Test serving uploaded files"""
        success, details, response = self.make_request('GET', f'shares/files/{filename}')
        
        # For file serving, we expect different response handling
        url = f"{self.api_url}/shares/files/{filename}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            response = requests.get(url, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', 'unknown')
                content_length = len(response.content)
                self.log_test(f"Get file: {filename}", True, f"File served, type: {content_type}, size: {content_length} bytes")
            else:
                self.log_test(f"Get file: {filename}", False, f"Status: {response.status_code}")
            
            return success

        except requests.exceptions.RequestException as e:
            self.log_test(f"Get file: {filename}", False, f"Request failed: {str(e)}")
            return False

    def test_get_nonexistent_file(self):
        """Test serving non-existent file"""
        success, details, response = self.make_request('GET', 'shares/files/nonexistent.txt', expected_status=404)
        self.log_test("Non-existent file rejection", success, details)
        return success

    def test_update_share(self, share_id, title=None, description=None, content=None):
        """Test updating a share"""
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if content is not None:
            update_data['content'] = content

        success, details, response = self.make_request('PUT', f'shares/{share_id}', update_data)
        
        self.log_test(f"Update share: {share_id}", success, details)
        return success

    def test_update_nonexistent_share(self):
        """Test updating non-existent share"""
        success, details, response = self.make_request(
            'PUT', 'shares/nonexistent-id',
            {'title': 'Updated Title'},
            expected_status=404
        )
        
        self.log_test("Update non-existent share rejection", success, details)
        return success

    def test_update_others_share(self, share_id):
        """Test updating another user's share (should fail)"""
        success, details, response = self.make_request(
            'PUT', f'shares/{share_id}',
            {'title': 'Unauthorized Update'},
            expected_status=403
        )
        
        self.log_test("Update others' share rejection", success, details)
        return success

    def test_delete_share(self, share_id):
        """Test deleting a share"""
        success, details, response = self.make_request('DELETE', f'shares/{share_id}')
        
        if success:
            # Remove from tracking list
            if share_id in self.created_shares:
                self.created_shares.remove(share_id)
        
        self.log_test(f"Delete share: {share_id}", success, details)
        return success

    def test_delete_nonexistent_share(self):
        """Test deleting non-existent share"""
        success, details, response = self.make_request(
            'DELETE', 'shares/nonexistent-id',
            expected_status=404
        )
        
        self.log_test("Delete non-existent share rejection", success, details)
        return success

    def test_delete_others_share(self, share_id):
        """Test deleting another user's share (should fail)"""
        success, details, response = self.make_request(
            'DELETE', f'shares/{share_id}',
            expected_status=403
        )
        
        self.log_test("Delete others' share rejection", success, details)
        return success

    def cleanup_created_shares(self):
        """Clean up any remaining created shares"""
        for share_id in self.created_shares[:]:  # Create a copy to iterate over
            self.test_delete_share(share_id)

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting LearnTrack Hierarchical API Testing Suite")
        print("=" * 60)
        
        # Test 1: Invalid login
        print("\n📋 Testing Authentication Security")
        self.test_invalid_login()
        
        # Test 2: Valid login
        print("\n📋 Testing Valid Authentication")
        if not self.test_login("giatk", "giatk"):
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
        
        # Create, update, and delete a test note with hierarchical context - use Page resource
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
                    
                    note_id = self.test_create_note(test_resource, test_module, test_session, 
                                                   "Test note for hierarchical learning structure")
                    
                    if note_id:
                        self.test_update_note(note_id, "Updated test note for hierarchical structure")
                        self.test_delete_note(note_id)
        
        # Test invalid note creation
        self.test_invalid_note_creation()
        
        # Test 9: Comprehensive Sharing System Tests
        print("\n📋 Testing Sharing System")
        
        # Test empty shares initially
        self.test_get_shares_empty()
        
        # Test URL share creation
        url_share_id = self.test_create_url_share(
            "Learning React Documentation", 
            "Official React documentation for learning modern web development",
            "https://react.dev/learn"
        )
        
        # Test another URL share
        url_share_id2 = self.test_create_url_share(
            "FastAPI Tutorial",
            "Complete guide to building APIs with FastAPI",
            "https://fastapi.tiangolo.com/tutorial/"
        )
        
        # Test invalid URL creation
        self.test_create_invalid_url_share()
        self.test_create_file_share_via_url_endpoint()
        
        # Test file uploads
        pdf_share_id = self.test_upload_file_share(
            "Learning Guide PDF",
            "Comprehensive learning guide for web development",
            "learning_guide.pdf",
            "This is a sample PDF content for testing file upload functionality.",
            "application/pdf"
        )
        
        txt_share_id = self.test_upload_file_share(
            "Notes Text File",
            "Personal notes and reminders",
            "notes.txt",
            "These are my personal learning notes:\n1. Learn React\n2. Master FastAPI\n3. Build projects",
            "text/plain"
        )
        
        # Test invalid file uploads
        self.test_upload_invalid_file_type()
        self.test_upload_large_file()
        
        # Test pagination and filtering
        self.test_get_shares_with_pagination(1, 2)
        self.test_get_shares_with_pagination(2, 2)
        
        # Test search functionality
        self.test_search_shares("React")
        self.test_search_shares("learning")
        self.test_search_shares("nonexistent")
        
        # Test type filtering
        self.test_filter_shares_by_type("all")
        self.test_filter_shares_by_type("url")
        self.test_filter_shares_by_type("file")
        
        # Test file serving (if we have uploaded files)
        if pdf_share_id:
            # Get the share to find the filename
            success, details, response = self.make_request('GET', 'shares')
            if success and 'items' in response:
                for share in response['items']:
                    if share.get('id') == pdf_share_id and share.get('type') == 'file':
                        filename = share.get('content')
                        if filename:
                            self.test_get_file(filename)
                        break
        
        # Test non-existent file
        self.test_get_nonexistent_file()
        
        # Test share updates
        if url_share_id:
            self.test_update_share(url_share_id, 
                                 title="Updated React Documentation",
                                 description="Updated description for React docs",
                                 content="https://react.dev/learn/start-a-new-react-project")
        
        # Test update validations
        self.test_update_nonexistent_share()
        
        # Test 10: Multi-User Sharing Tests
        print("\n📋 Testing Multi-User Sharing Functionality")
        
        # Create share as current user for permission testing
        admin_share_id = self.test_create_url_share(
            "Admin Only Share",
            "This share belongs to admin user",
            "https://admin-only-resource.com"
        )
        
        # Switch to different user
        if self.test_login("trieupn", "trieupn"):
            # Test accessing shares as different user
            self.test_get_shares_with_pagination(1, 10)
            
            # Create share as user1
            user1_share_id = self.test_create_url_share(
                "User1 Learning Resource",
                "Resource shared by user1",
                "https://user1-resource.com"
            )
            
            # Test permission restrictions - try to update admin's share
            if admin_share_id:
                self.test_update_others_share(admin_share_id)
                self.test_delete_others_share(admin_share_id)
            
            # Clean up user1's share
            if user1_share_id:
                self.test_delete_share(user1_share_id)
        
        # Switch back to admin for cleanup
        if self.test_login("giatk", "giatk"):
            # Test delete validations
            self.test_delete_nonexistent_share()
            
            # Clean up remaining shares
            self.cleanup_created_shares()
        
        # Test 11: Test with different user
        print("\n📋 Testing Multi-User Functionality")
        if self.test_login("user1", "pass1"):
            self.test_get_my_progress()
            
            # Test creating note as different user - use Book resource
            if structure and structure['resources']:
                # Find Book resource for testing
                book_resource = None
                for resource in structure['resources']:
                    if resource['name'] == 'Book':
                        book_resource = resource
                        break
                
                if book_resource and book_resource['modules']:
                    test_resource = book_resource['name']
                    test_module = book_resource['modules'][0]['name']
                    if book_resource['modules'][0]['sessions']:
                        test_session = book_resource['modules'][0]['sessions'][0]['name']
                        
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