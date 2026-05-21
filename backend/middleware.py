import time
from functools import wraps
from flask import request, jsonify, g
import requests
from config import Config

# In-memory storage for rate limiting
# Format: { key: [timestamps] }
api_limits = {}
ai_limits = {}

def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr or "unknown_ip"

def rate_limit_api(limit=Config.RATE_LIMIT_API_PER_MINUTE, window=60):
    """Rate limit API requests (default: 100 per minute)"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Use user_id if authenticated, else IP
            key = getattr(g, "user_id", None) or get_client_ip()
            now = time.time()
            
            # Clean old requests
            if key not in api_limits:
                api_limits[key] = []
            api_limits[key] = [t for t in api_limits[key] if now - t < window]
            
            if len(api_limits[key]) >= limit:
                return jsonify({
                    "error": "Too Many Requests",
                    "message": f"API rate limit exceeded. Max {limit} requests per {window} seconds."
                }), 429
                
            api_limits[key].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def rate_limit_ai(limit=Config.RATE_LIMIT_AI_PER_HOUR, window=3600):
    """Rate limit AI generations (default: 10 per hour)"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # AI generation requires user authentication
            user_id = getattr(g, "user_id", None)
            if not user_id:
                return jsonify({"error": "Unauthorized", "message": "Authentication required for AI generation"}), 401
                
            now = time.time()
            
            # Clean old requests
            if user_id not in ai_limits:
                ai_limits[user_id] = []
            ai_limits[user_id] = [t for t in ai_limits[user_id] if now - t < window]
            
            if len(ai_limits[user_id]) >= limit:
                return jsonify({
                    "error": "Rate Limit Exceeded",
                    "message": f"AI generation limit exceeded. Max {limit} generations per hour."
                }), 429
                
            ai_limits[user_id].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def token_required(f):
    """Authenticate request using Supabase JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"].split(" ")
            if len(auth_header) == 2 and auth_header[0] == "Bearer":
                token = auth_header[1]
                
        if not token:
            return jsonify({"error": "Unauthorized", "message": "Access token is missing"}), 401
            
        # Development / Test Mock Tokens
        if token == "mock-admin-token":
            g.user_id = "mock-admin-id"
            g.email = "admin@taskhub.dev"
            g.role = "admin"
            g.token = token
            return f(*args, **kwargs)
        elif token == "mock-user-token":
            g.user_id = "mock-user-id"
            g.email = "user@taskhub.dev"
            g.role = "user"
            g.token = token
            return f(*args, **kwargs)
            
        try:
            # Query Supabase Auth endpoint using the bearer token to verify it
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": Config.SUPABASE_ANON_KEY
            }
            res = requests.get(f"{Config.SUPABASE_URL}/auth/v1/user", headers=headers, timeout=5)
            
            if res.status_code != 200:
                return jsonify({"error": "Unauthorized", "message": "Invalid or expired session"}), 401
                
            user_data = res.json()
            g.user_id = user_data["id"]
            g.email = user_data["email"]
            g.token = token
            
            # Fetch user role from public.users table in Supabase
            role_headers = {
                "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}"
            }
            role_url = f"{Config.SUPABASE_URL}/rest/v1/users?id=eq.{g.user_id}"
            role_res = requests.get(role_url, headers=role_headers, timeout=5)
            
            if role_res.status_code == 200 and role_res.json():
                g.role = role_res.json()[0].get("role", "user")
            else:
                # Default role
                g.role = "user"
                
        except Exception as e:
            return jsonify({"error": "Unauthorized", "message": f"Auth verification failed: {str(e)}"}), 401
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Enforce admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(g, "role", None) != "admin":
            return jsonify({"error": "Forbidden", "message": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated
