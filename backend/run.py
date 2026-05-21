from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    print(f"Starting TaskHub Flask Backend on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
