from flask import Blueprint, jsonify, g, request
import requests
import unittest.mock
from config import Config
from middleware import token_required, admin_required, rate_limit_api
from services.email_service import EmailService
from services.mock_db import MockDB

tasks_bp = Blueprint("tasks", __name__)

def is_offline():
    # If requests is mocked (like in unit tests), then we are NOT offline (we let the mock run)
    if (isinstance(requests.get, unittest.mock.Mock) or 
        isinstance(requests.post, unittest.mock.Mock) or 
        isinstance(requests.patch, unittest.mock.Mock) or 
        isinstance(requests.delete, unittest.mock.Mock)):
        return False
    # Otherwise, if mock token or default Supabase URL, we are offline
    return getattr(g, "user_id", "").startswith("mock-") or Config.SUPABASE_URL == "https://your-project.supabase.co"

def log_audit(table_name, action, row_id, old_data=None, new_data=None):
    """Helper to write database mutations to audit_logs table"""
    if is_offline():
        MockDB.log_audit(table_name, action, row_id, old_data, new_data, getattr(g, "user_id", "system"))
        return
        
    try:
        db_headers = {
            "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "table_name": table_name,
            "action": action,
            "row_id": str(row_id),
            "performed_by": getattr(g, "user_id", "system"),
            "old_data": old_data,
            "new_data": new_data
        }
        requests.post(f"{Config.SUPABASE_URL}/rest/v1/audit_logs", json=payload, headers=db_headers, timeout=5)
    except Exception as e:
        print(f"Audit log failed: {str(e)}")

# ==========================================
# ADMIN TASKS API
# ==========================================

@tasks_bp.route("", methods=["POST"])
@admin_required
@rate_limit_api()
def create_task():
    """Admin creates a task with product image attached"""
    data = request.json
    if not data or "title" not in data or "product_image_url" not in data:
        return jsonify({"error": "Bad Request", "message": "Title and product_image_url are required"}), 400
        
    if is_offline():
        task = MockDB.create_task(
            title=data["title"],
            description=data.get("description", ""),
            product_image_url=data["product_image_url"],
            created_by=g.user_id,
            assigned_to=data.get("assigned_to", None)
        )
        if task["assigned_to"]:
            cls_notify_assign(task)
        return jsonify(task), 201
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "title": data["title"],
        "description": data.get("description", ""),
        "product_image_url": data["product_image_url"],
        "status": "pending",
        "created_by": g.user_id,
        "assigned_to": data.get("assigned_to", None)
    }
    
    if payload["assigned_to"]:
        payload["status"] = "assigned"
        
    res = requests.post(f"{Config.SUPABASE_URL}/rest/v1/tasks", json=payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201]:
        task = res.json()[0]
        log_audit("tasks", "CREATE", task["id"], None, task)
        
        # If assigned, send email notification
        if task["assigned_to"]:
            cls_notify_assign(task)
            
        return jsonify(task), 201
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("", methods=["GET"])
@admin_required
@rate_limit_api()
def list_all_tasks():
    """Admin: List all tasks on the platform"""
    if is_offline():
        return jsonify(MockDB.get_all_tasks()), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
    }
    res = requests.get(f"{Config.SUPABASE_URL}/rest/v1/tasks?select=*,assigned_to:users(email,full_name)&order=created_at.desc", headers=db_headers, timeout=5)
    
    if res.status_code == 200:
        return jsonify(res.json()), 200
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>/assign", methods=["POST"])
@admin_required
@rate_limit_api()
def assign_task(task_id):
    """Admin assigns task to a specific user"""
    data = request.json
    if not data or "assigned_to" not in data:
        return jsonify({"error": "Bad Request", "message": "assigned_to field is required"}), 400
        
    if is_offline():
        new_task = MockDB.assign_task(task_id, data["assigned_to"], g.user_id)
        if not new_task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        cls_notify_assign(new_task)
        return jsonify(new_task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Get current task to check old state
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    old_task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if old_task_res.status_code != 200 or not old_task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    old_task = old_task_res.json()[0]
    
    update_payload = {
        "assigned_to": data["assigned_to"],
        "status": "assigned"
    }
    
    res = requests.patch(task_url, json=update_payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201] and res.json():
        new_task = res.json()[0]
        log_audit("tasks", "UPDATE", task_id, old_task, new_task)
        
        # Email notification
        cls_notify_assign(new_task)
        
        return jsonify(new_task), 200
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>/accept", methods=["PUT"])
@admin_required
@rate_limit_api()
def accept_task(task_id):
    """Admin reviews and accepts task (completed)"""
    if is_offline():
        new_task = MockDB.update_task_status(task_id, "accepted", g.user_id)
        if not new_task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        cls_notify_status(new_task, "accepted")
        return jsonify(new_task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    old_task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if old_task_res.status_code != 200 or not old_task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    old_task = old_task_res.json()[0]
    
    update_payload = {"status": "accepted"}
    res = requests.patch(task_url, json=update_payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201] and res.json():
        new_task = res.json()[0]
        log_audit("tasks", "UPDATE", task_id, old_task, new_task)
        
        # Notify User
        cls_notify_status(new_task, "accepted")
        
        return jsonify(new_task), 200
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>/request-revision", methods=["PUT"])
@admin_required
@rate_limit_api()
def request_revision(task_id):
    """Admin requests revision with feedback"""
    data = request.json or {}
    revision_notes = data.get("feedback", "Please refine product image alignments and lighting consistency.")
    
    if is_offline():
        new_task = MockDB.update_task_status(task_id, "revision_requested", g.user_id, revision_notes)
        if not new_task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        cls_notify_status(new_task, "revision_requested", revision_notes)
        return jsonify(new_task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    old_task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if old_task_res.status_code != 200 or not old_task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    old_task = old_task_res.json()[0]
    
    update_payload = {
        "status": "revision_requested",
        "revision_notes": revision_notes
    }
    res = requests.patch(task_url, json=update_payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201] and res.json():
        new_task = res.json()[0]
        log_audit("tasks", "UPDATE", task_id, old_task, new_task)
        
        # Notify User
        cls_notify_status(new_task, "revision_requested", revision_notes)
        
        return jsonify(new_task), 200
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>", methods=["DELETE"])
@admin_required
@rate_limit_api()
def delete_task(task_id):
    """Admin deletes a task"""
    if is_offline():
        deleted = MockDB.delete_task(task_id, g.user_id)
        if not deleted:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        return jsonify({"message": "Task deleted successfully"}), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Prefer": "return=representation"
    }
    
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    res = requests.delete(task_url, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 204]:
        log_audit("tasks", "DELETE", task_id, None, None)
        return jsonify({"message": "Task deleted successfully"}), 200
    return jsonify({"error": "Database Error", "message": res.text}), 500

# ==========================================
# USER TASKS API
# ==========================================

@tasks_bp.route("/my-tasks", methods=["GET"])
@token_required
@rate_limit_api()
def list_my_tasks():
    """User views their own assigned tasks"""
    if is_offline():
        return jsonify(MockDB.get_my_tasks(g.user_id)), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
    }
    url = f"{Config.SUPABASE_URL}/rest/v1/tasks?assigned_to=eq.{g.user_id}&order=created_at.desc"
    res = requests.get(url, headers=db_headers, timeout=5)
    
    if res.status_code == 200:
        return jsonify(res.json()), 200
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>", methods=["GET"])
@token_required
@rate_limit_api()
def get_task_detail(task_id):
    """View task details and generated images"""
    if is_offline():
        task = MockDB.get_task(task_id)
        if not task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
            
        # Enforce access control: only assignee or admins can view
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
            
        return jsonify(task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
    }
    
    # Fetch task
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    task_res = requests.get(task_url, headers=db_headers, timeout=5)
    
    if task_res.status_code != 200 or not task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        
    task = task_res.json()[0]
    
    # Enforce access control: only assignee or admins can view
    if g.role != "admin" and task.get("assigned_to") != g.user_id:
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        
    return jsonify(task), 200

@tasks_bp.route("/<uuid:task_id>/start", methods=["PUT"])
@token_required
@rate_limit_api()
def start_task(task_id):
    """User clicks start to move status from assigned to in_progress"""
    if is_offline():
        task = MockDB.get_task(task_id)
        if not task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
            
        new_task = MockDB.update_task_status(task_id, "in_progress", g.user_id)
        return jsonify(new_task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    old_task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if old_task_res.status_code != 200 or not old_task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    old_task = old_task_res.json()[0]
    
    if g.role != "admin" and old_task.get("assigned_to") != g.user_id:
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        
    update_payload = {"status": "in_progress"}
    res = requests.patch(task_url, json=update_payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201] and res.json():
        new_task = res.json()[0]
        log_audit("tasks", "UPDATE", task_id, old_task, new_task)
        return jsonify(new_task), 200
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

@tasks_bp.route("/<uuid:task_id>/submit", methods=["POST"])
@token_required
@rate_limit_api()
def submit_task(task_id):
    """User submits the task for admin review after generating all 8 images"""
    if is_offline():
        task = MockDB.get_task(task_id)
        if not task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
            
        generations = MockDB.get_task_generations(task_id)
        if len(generations) < 8:
            return jsonify({
                "error": "Submission Rejected",
                "message": f"You must finalize all 8 required image variations before submitting. Found {len(generations)}/8."
            }), 400
            
        new_task = MockDB.update_task_status(task_id, "submitted", g.user_id)
        
        # Email notification to Admin
        try:
            user_name = "Demo Photographer User" if g.user_id == "mock-user-id" else g.email
            EmailService.send_task_submitted(Config.ADMIN_EMAIL, user_name, new_task["title"], task_id)
        except Exception as e:
            print(f"Failed to send email to admin: {str(e)}")
            
        return jsonify(new_task), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    old_task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if old_task_res.status_code != 200 or not old_task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
    old_task = old_task_res.json()[0]
    
    if g.role != "admin" and old_task.get("assigned_to") != g.user_id:
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        
    # Verify that exactly 8 variations have been generated/finalized
    gens_url = f"{Config.SUPABASE_URL}/rest/v1/generated_images?task_id=eq.{task_id}"
    gens_res = requests.get(gens_url, headers=db_headers, timeout=5)
    
    if gens_res.status_code != 200:
        return jsonify({"error": "Database Error", "message": "Could not verify generations"}), 500
        
    generations = gens_res.json()
    if len(generations) < 8:
        return jsonify({
            "error": "Submission Rejected",
            "message": f"You must finalize all 8 required image variations before submitting. Found {len(generations)}/8."
        }), 400
        
    update_payload = {"status": "submitted"}
    res = requests.patch(task_url, json=update_payload, headers=db_headers, timeout=5)
    
    if res.status_code in [200, 201] and res.json():
        new_task = res.json()[0]
        log_audit("tasks", "UPDATE", task_id, old_task, new_task)
        
        # Email notification to Admin
        try:
            # Fetch user name for the email
            user_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{g.user_id}"
            user_res = requests.get(user_url, headers=db_headers, timeout=5)
            user_name = user_res.json()[0].get("full_name", g.email) if user_res.status_code == 200 and user_res.json() else g.email
            
            EmailService.send_task_submitted(Config.ADMIN_EMAIL, user_name, new_task["title"], task_id)
        except Exception as e:
            print(f"Failed to send email to admin: {str(e)}")
            
        return jsonify(new_task), 200
        
    return jsonify({"error": "Database Error", "message": res.text}), 500

# ==========================================
# HELPER NOTIFICATION DISPATCHERS
# ==========================================

def cls_notify_assign(task):
    """Sends email when task is assigned"""
    if is_offline():
        try:
            user_email = "user@taskhub.dev" if task['assigned_to'] == "mock-user-id" else "unknown@taskhub.dev"
            user_name = "Demo Photographer User" if task['assigned_to'] == "mock-user-id" else "Unknown User"
            EmailService.send_task_assigned(
                user_email,
                user_name,
                task["title"],
                task["id"],
                task["product_image_url"]
            )
        except Exception as e:
            print(f"Assignment email failed: {str(e)}")
        return
        
    try:
        db_headers = {
            "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
        }
        # Fetch user email and full_name
        user_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{task['assigned_to']}"
        user_res = requests.get(user_url, headers=db_headers, timeout=5)
        
        if user_res.status_code == 200 and user_res.json():
            user = user_res.json()[0]
            EmailService.send_task_assigned(
                user["email"],
                user.get("full_name", user["email"]),
                task["title"],
                task["id"],
                task["product_image_url"]
            )
    except Exception as e:
        print(f"Assignment email failed: {str(e)}")

def cls_notify_status(task, status, feedback=""):
    """Sends email for status updates (accepted/revision_requested)"""
    if is_offline():
        try:
            user_email = "user@taskhub.dev" if task['assigned_to'] == "mock-user-id" else "unknown@taskhub.dev"
            user_name = "Demo Photographer User" if task['assigned_to'] == "mock-user-id" else "Unknown User"
            EmailService.send_task_status_update(
                user_email,
                user_name,
                task["title"],
                task["id"],
                status,
                feedback
            )
        except Exception as e:
            print(f"Status update email failed: {str(e)}")
        return
        
    try:
        db_headers = {
            "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
        }
        # Fetch user
        user_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{task['assigned_to']}"
        user_res = requests.get(user_url, headers=db_headers, timeout=5)
        
        if user_res.status_code == 200 and user_res.json():
            user = user_res.json()[0]
            EmailService.send_task_status_update(
                user["email"],
                user.get("full_name", user["email"]),
                task["title"],
                task["id"],
                status,
                feedback
            )
    except Exception as e:
        print(f"Status update email failed: {str(e)}")
