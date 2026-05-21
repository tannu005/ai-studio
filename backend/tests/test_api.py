import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import sys
import os

# Add parent directories to path to import app and routes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import Config
from worker import JobManager

class TaskHubAPITestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Clear rate limits and jobs for tests
        import middleware
        middleware.api_limits.clear()
        middleware.ai_limits.clear()
        
        self.job_manager = JobManager()
        self.job_manager.jobs.clear()

    def tearDown(self):
        self.app_context.pop()

    def test_health_check(self):
        """Test that health check endpoint returns 200 and healthy status"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'TaskHub Flask Backend')

    def test_auth_me_unauthorized(self):
        """Test that accessing /api/auth/me without token returns 401"""
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Unauthorized')

    def test_auth_me_mock_admin(self):
        """Test that accessing /api/auth/me with mock-admin-token returns mock admin details"""
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': 'Bearer mock-admin-token'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['id'], 'mock-admin-id')
        self.assertEqual(data['email'], 'admin@taskhub.dev')
        self.assertEqual(data['role'], 'admin')

    def test_auth_me_mock_user(self):
        """Test that accessing /api/auth/me with mock-user-token returns mock user details"""
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': 'Bearer mock-user-token'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['id'], 'mock-user-id')
        self.assertEqual(data['email'], 'user@taskhub.dev')
        self.assertEqual(data['role'], 'user')

    @patch('routes.tasks.requests.get')
    def test_list_all_tasks_as_admin(self, mock_get):
        """Test that admin can retrieve all tasks on the platform"""
        # Mock the Supabase DB response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": str(uuid.uuid4()),
                "title": "Jewelry Shoot 1",
                "description": "Premium pearl ring shoot",
                "product_image_url": "https://example.com/ring.jpg",
                "status": "pending",
                "assigned_to": None,
                "created_by": "mock-admin-id"
            }
        ]
        mock_get.return_value = mock_response

        response = self.client.get(
            '/api/tasks',
            headers={'Authorization': 'Bearer mock-admin-token'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "Jewelry Shoot 1")

    def test_list_all_tasks_as_user_forbidden(self):
        """Test that standard user is forbidden from retrieving admin task list"""
        response = self.client.get(
            '/api/tasks',
            headers={'Authorization': 'Bearer mock-user-token'}
        )
        self.assertEqual(response.status_code, 403)

    @patch('routes.tasks.requests.post')
    def test_create_task_as_admin(self, mock_post):
        """Test that admin can create tasks successfully"""
        task_id = str(uuid.uuid4())
        
        # Mock database insertion response
        mock_res_db = MagicMock()
        mock_res_db.status_code = 201
        mock_res_db.json.return_value = [{
            "id": task_id,
            "title": "Luxury Necklace Shoot",
            "description": "Generate 8 variations",
            "product_image_url": "https://example.com/necklace.jpg",
            "status": "pending",
            "assigned_to": None,
            "created_by": "mock-admin-id"
        }]
        
        # We also mock audit log post
        mock_post.return_value = mock_res_db

        payload = {
            "title": "Luxury Necklace Shoot",
            "description": "Generate 8 variations",
            "product_image_url": "https://example.com/necklace.jpg"
        }
        
        response = self.client.post(
            '/api/tasks',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock-admin-token'}
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['id'], task_id)
        self.assertEqual(data['title'], "Luxury Necklace Shoot")

    @patch('routes.tasks.requests.get')
    def test_list_my_tasks_as_user(self, mock_get):
        """Test that user can list tasks assigned to them"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": str(uuid.uuid4()),
                "title": "User Assigned Task",
                "description": "Shoot pearl jewelry",
                "product_image_url": "https://example.com/necklace.jpg",
                "status": "assigned",
                "assigned_to": "mock-user-id"
            }
        ]
        mock_get.return_value = mock_response

        response = self.client.get(
            '/api/tasks/my-tasks',
            headers={'Authorization': 'Bearer mock-user-token'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], "User Assigned Task")

    @patch('routes.tasks.requests.patch')
    @patch('routes.tasks.requests.get')
    def test_start_task_by_user(self, mock_get, mock_patch):
        """Test that user can start an assigned task (changing status to in_progress)"""
        task_id = str(uuid.uuid4())
        
        # Mock get task
        mock_get_res = MagicMock()
        mock_get_res.status_code = 200
        mock_get_res.json.return_value = [{
            "id": task_id,
            "title": "Jewelry Shoot",
            "status": "assigned",
            "assigned_to": "mock-user-id"
        }]
        mock_get.return_value = mock_get_res

        # Mock patch task status
        mock_patch_res = MagicMock()
        mock_patch_res.status_code = 200
        mock_patch_res.json.return_value = [{
            "id": task_id,
            "title": "Jewelry Shoot",
            "status": "in_progress",
            "assigned_to": "mock-user-id"
        }]
        mock_patch.return_value = mock_patch_res

        response = self.client.put(
            f'/api/tasks/{task_id}/start',
            headers={'Authorization': 'Bearer mock-user-token'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'in_progress')

    @patch('routes.generate.requests.get')
    @patch('worker.requests.get')
    def test_trigger_generation_job(self, mock_worker_get, mock_gen_get):
        """Test triggering a background AI generation job"""
        task_id = str(uuid.uuid4())
        
        # Mock task check in trigger_generation
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = [{
            "id": task_id,
            "title": "Pearl Bracelet Shoot",
            "product_image_url": "https://example.com/bracelet.jpg",
            "status": "in_progress",
            "assigned_to": "mock-user-id"
        }]
        mock_gen_get.return_value = mock_res
        
        # Mock image download in worker thread
        mock_img_res = MagicMock()
        mock_img_res.status_code = 200
        mock_img_res.content = b"fake-image-bytes"
        mock_worker_get.return_value = mock_img_res

        payload = {
            "image_type": "white_bg",
            "prompt_used": "white backdrop jewelry studio"
        }

        # We patch start_job so it doesn't try to make DB edits or download during unit tests synchronously
        with patch.object(self.job_manager, 'start_job') as mock_start_job:
            response = self.client.post(
                f'/api/tasks/{task_id}/generate',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'Authorization': 'Bearer mock-user-token'}
            )
            
            self.assertEqual(response.status_code, 202)
            data = json.loads(response.data.decode('utf-8'))
            self.assertEqual(data['message'], "AI Generation job queued")
            self.assertIn('job_id', data)
            self.assertEqual(data['status'], 'pending')
            
            # Check that job was correctly created and tracked in memory
            job_id = data['job_id']
            job = self.job_manager.get_job(job_id)
            self.assertIsNotNone(job)
            self.assertEqual(job['task_id'], task_id)
            self.assertEqual(job['image_type'], 'white_bg')

if __name__ == '__main__':
    unittest.main()
