import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

# Initialize blueprints
from routes.auth import auth_bp
from routes.tasks import tasks_bp
from routes.generate import generate_bp

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    
    # Configure CORS to allow Next.js development client
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
    
    # App configs
    app.config.from_object(Config)
    
    # Ensure static directories for generated images exist
    static_dir = os.path.join(app.root_path, "static", "generations")
    os.makedirs(static_dir, exist_ok=True)
    
    # Register blueprints under exact prefix matches
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks") # For /api/tasks and /api/tasks/my-tasks
    app.register_blueprint(generate_bp, url_prefix="/api")   # For /api/tasks/:id/generate, /api/jobs/:id/status
    
    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e.description)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found", "message": "The requested resource could not be found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500
        
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "TaskHub Flask Backend"}), 200
        
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
