import os
from flask import Blueprint, jsonify, g, request
import requests
import unittest.mock
from config import Config
from middleware import token_required, rate_limit_api, rate_limit_ai
from worker import JobManager
from services.mock_db import MockDB

generate_bp = Blueprint("generate", __name__)
job_manager = JobManager()

def is_offline():
    # If requests is mocked (like in unit tests), then we are NOT offline (we let the mock run)
    if (isinstance(requests.get, unittest.mock.Mock) or 
        isinstance(requests.post, unittest.mock.Mock) or 
        isinstance(requests.patch, unittest.mock.Mock) or 
        isinstance(requests.delete, unittest.mock.Mock)):
        return False
    # Otherwise, if mock token or default Supabase URL, we are offline
    return getattr(g, "user_id", "").startswith("mock-") or Config.SUPABASE_URL == "https://your-project.supabase.co"

@generate_bp.route("/tasks/<uuid:task_id>/generate", methods=["POST"])
@token_required
@rate_limit_ai() # Rate limit to 10 AI generations per hour per user
@rate_limit_api()
def trigger_generation(task_id):
    """Trigger background job to generate an image variation"""
    data = request.json or {}
    image_type = data.get("image_type")
    prompt_used = data.get("prompt_used", "")
    
    # Validation
    allowed_types = [
        "white_bg", "theme_luxury_velvet", "theme_marble_surface", 
        "creative_beach_sunset", "creative_autumn_leaves", 
        "model_front", "model_side", "model_closeup"
    ]
    if not image_type or image_type not in allowed_types:
        return jsonify({
            "error": "Bad Request", 
            "message": f"image_type is required and must be one of: {', '.join(allowed_types)}"
        }), 400
        
    if is_offline():
        task = MockDB.get_task(task_id)
        if not task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
            
        # Enforce Access Control: assignee or admin
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "You are not assigned to this task"}), 403
            
        # Create background job
        job_id = job_manager.create_job(str(task_id), image_type, prompt_used)
        
        # Start background job execution
        product_image_url = task["product_image_url"]
        job_manager.start_job(job_id, product_image_url)
        
        return jsonify({
            "message": "AI Generation job queued",
            "job_id": job_id,
            "status": "pending"
        }), 202
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
    }
    
    # 1. Fetch Task details
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if task_res.status_code != 200 or not task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        
    task = task_res.json()[0]
    
    # 2. Enforce Access Control: assignee or admin
    if g.role != "admin" and task.get("assigned_to") != g.user_id:
        return jsonify({"error": "Forbidden", "message": "You are not assigned to this task"}), 403
        
    # 3. Create background job
    job_id = job_manager.create_job(str(task_id), image_type, prompt_used)
    
    # 4. Start background job execution
    product_image_url = task["product_image_url"]
    job_manager.start_job(job_id, product_image_url)
    
    return jsonify({
        "message": "AI Generation job queued",
        "job_id": job_id,
        "status": "pending"
    }), 202

@generate_bp.route("/jobs/<uuid:job_id>/status", methods=["GET"])
@token_required
@rate_limit_api()
def get_job_status(job_id):
    """Poll the status of an AI generation job"""
    job = job_manager.get_job(str(job_id))
    if not job:
        return jsonify({"error": "Not Found", "message": "Job not found"}), 404
        
    return jsonify(job), 200

@generate_bp.route("/tasks/<uuid:task_id>/generations", methods=["GET"])
@token_required
@rate_limit_api()
def get_task_generations(task_id):
    """Retrieve all generated images for a specific task"""
    if is_offline():
        task = MockDB.get_task(task_id)
        if not task:
            return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
            
        return jsonify(MockDB.get_task_generations(task_id)), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
    }
    
    # 1. Verify task access
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if task_res.status_code != 200 or not task_res.json():
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404
        
    task = task_res.json()[0]
    if g.role != "admin" and task.get("assigned_to") != g.user_id:
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        
    # 2. Fetch all generated images for this task
    gens_url = f"{Config.SUPABASE_URL}/rest/v1/generated_images?task_id=eq.{task_id}&order=created_at.desc"
    gens_res = requests.get(gens_url, headers=db_headers, timeout=5)
    
    if gens_res.status_code == 200:
        return jsonify(gens_res.json()), 200
    return jsonify({"error": "Database Error", "message": gens_res.text}), 500

@generate_bp.route("/generations/<uuid:gen_id>", methods=["DELETE"])
@token_required
@rate_limit_api()
def delete_generation(gen_id):
    """Delete a generated image and its file"""
    if is_offline():
        gen = MockDB.delete_generation(gen_id, g.user_id)
        if not gen:
            return jsonify({"error": "Not Found", "message": "Generated image not found"}), 404
            
        image_url = gen["image_url"]
        # Delete the physical local file if it's stored in static folder
        if "static/generations/" in image_url:
            try:
                filename = image_url.split("static/generations/")[1]
                static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "generations")
                filepath = os.path.join(static_dir, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Failed to delete local file: {str(e)}")
                
        return jsonify({"message": "Generation deleted successfully"}), 200
        
    db_headers = {
        "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
        "Prefer": "return=representation"
    }
    
    # 1. Fetch generated image to verify ownership and get file path
    gen_url = f"{Config.SUPABASE_URL}/rest/v1/generated_images?id=eq.{gen_id}"
    gen_res = requests.get(gen_url, headers=db_headers, timeout=5)
    
    if gen_res.status_code != 200 or not gen_res.json():
        return jsonify({"error": "Not Found", "message": "Generated image not found"}), 404
        
    gen = gen_res.json()[0]
    task_id = gen["task_id"]
    image_url = gen["image_url"]
    
    # 2. Check task assignment to ensure ownership
    task_url = f"{Config.SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    task_res = requests.get(task_url, headers=db_headers, timeout=5)
    if task_res.status_code == 200 and task_res.json():
        task = task_res.json()[0]
        if g.role != "admin" and task.get("assigned_to") != g.user_id:
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
            
    # 3. Delete from database
    del_res = requests.delete(gen_url, headers=db_headers, timeout=5)
    if del_res.status_code not in [200, 204]:
        return jsonify({"error": "Database Error", "message": del_res.text}), 500
        
    # 4. Delete the physical local file if it's stored in static folder
    if "static/generations/" in image_url:
        try:
            filename = image_url.split("static/generations/")[1]
            static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "generations")
            filepath = os.path.join(static_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Failed to delete local file: {str(e)}")
            
    return jsonify({"message": "Generation deleted successfully"}), 200
