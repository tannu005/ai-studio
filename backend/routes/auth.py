from flask import Blueprint, jsonify, g, request
import requests
from config import Config
from middleware import token_required, rate_limit_api

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/oauth/callback", methods=["POST"])
@rate_limit_api()
def oauth_callback():
    """
    Sync user profile from Supabase JWT to the public.users table.
    Expects Bearer token in Authorization header.
    """
    token = None
    if "Authorization" in request.headers:
        auth_header = request.headers["Authorization"].split(" ")
        if len(auth_header) == 2 and auth_header[0] == "Bearer":
            token = auth_header[1]
            
    if not token:
        return jsonify({"error": "Unauthorized", "message": "Missing token"}), 401
        
    # Mock Auth for development/testing
    if token == "mock-admin-token":
        return jsonify({
            "message": "User synchronized successfully",
            "user": {"id": "mock-admin-id", "email": "admin@taskhub.dev", "role": "admin"}
        }), 200
    elif token == "mock-user-token":
        return jsonify({
            "message": "User synchronized successfully",
            "user": {"id": "mock-user-id", "email": "user@taskhub.dev", "role": "user"}
        }), 200
        
    try:
        # 1. Fetch user info from Supabase Auth
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": Config.SUPABASE_ANON_KEY
        }
        res = requests.get(f"{Config.SUPABASE_URL}/auth/v1/user", headers=headers, timeout=5)
        
        if res.status_code != 200:
            return jsonify({"error": "Unauthorized", "message": "Invalid token"}), 401
            
        user_data = res.json()
        user_id = user_data["id"]
        email = user_data["email"]
        
        # Extract metadata
        user_metadata = user_data.get("user_metadata", {})
        full_name = user_metadata.get("full_name", user_metadata.get("name", email.split("@")[0]))
        avatar_url = user_metadata.get("avatar_url", "")
        
        # 2. Check if user already exists in public.users table (bypass RLS using service role)
        db_headers = {
            "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        user_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
        check_res = requests.get(user_url, headers=db_headers, timeout=5)
        
        # Determine role: if email matches config's admin email or if they are the first user, make admin, else user
        role = "user"
        if email == Config.ADMIN_EMAIL:
            role = "admin"
            
        if check_res.status_code == 200 and check_res.json():
            # User exists, update profile
            existing_user = check_res.json()[0]
            role = existing_user.get("role", "user") # Keep existing role
            
            update_payload = {
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url
            }
            requests.patch(user_url, json=update_payload, headers=db_headers, timeout=5)
        else:
            # User does not exist, insert new profile
            # If no users exist yet, first user can be admin
            all_users_url = f"{Config.SUPABASE_URL}/rest/v1/users?select=id"
            all_users_res = requests.get(all_users_url, headers=db_headers, timeout=5)
            if all_users_res.status_code == 200 and len(all_users_res.json()) == 0:
                role = "admin"
                
            insert_payload = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url,
                "role": role
            }
            insert_url = f"{Config.SUPABASE_URL}/rest/v1/users"
            requests.post(insert_url, json=insert_payload, headers=db_headers, timeout=5)
            
        return jsonify({
            "message": "User synchronized successfully",
            "user": {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "avatar_url": avatar_url,
                "role": role
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": f"Sync failed: {str(e)}"}), 500

@auth_bp.route("/me", methods=["GET"])
@token_required
@rate_limit_api()
def me():
    """Return current authenticated user profile"""
    try:
        # Dev fallback
        if g.user_id in ["mock-admin-id", "mock-user-id"]:
            return jsonify({
                "id": g.user_id,
                "email": g.email,
                "full_name": "Mock User",
                "avatar_url": "",
                "role": g.role
            }), 200
            
        # Fetch user profile from public.users table
        db_headers = {
            "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
        }
        user_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{g.user_id}"
        res = requests.get(user_url, headers=db_headers, timeout=5)
        
        if res.status_code == 200 and res.json():
            return jsonify(res.json()[0]), 200
            
        # If profile doesn't exist in public.users yet, return current JWT info
        return jsonify({
            "id": g.user_id,
            "email": g.email,
            "role": "user"
        }), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@auth_bp.route("/logout", methods=["POST"])
@token_required
@rate_limit_api()
def logout():
    """Stateless logout (client deletes token, server returns success)"""
    return jsonify({"message": "Logout successful"}), 200
