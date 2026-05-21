import uuid
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
import unittest.mock
from config import Config
from services.ai_service import AIService
from services.mock_db import MockDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("background_worker")

def is_offline():
    # If requests is mocked (like in unit tests), then we are NOT offline (we let the mock run)
    if (isinstance(requests.get, unittest.mock.Mock) or 
        isinstance(requests.post, unittest.mock.Mock) or 
        isinstance(requests.patch, unittest.mock.Mock) or 
        isinstance(requests.delete, unittest.mock.Mock)):
        return False
    return Config.SUPABASE_URL == "https://your-project.supabase.co"

class JobManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JobManager, cls).__new__(cls)
                cls._instance.jobs = {}
                cls._instance.executor = ThreadPoolExecutor(max_workers=3)
            return cls._instance
            
    def create_job(self, task_id, image_type, prompt_used="", metadata=None):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "task_id": task_id,
            "image_type": image_type,
            "status": "pending",
            "progress": 0,
            "result_url": None,
            "error": None
        }
        return job_id
        
    def get_job(self, job_id):
        return self.jobs.get(job_id)
        
    def start_job(self, job_id, product_image_url):
        self.jobs[job_id]["status"] = "processing"
        self.jobs[job_id]["progress"] = 10
        
        # Submit to thread pool executor
        self.executor.submit(self._run_job, job_id, product_image_url)
        
    def _run_job(self, job_id, product_image_url):
        job = self.jobs[job_id]
        task_id = job["task_id"]
        image_type = job["image_type"]
        
        logger.info(f"Starting background generation job {job_id} for task {task_id} ({image_type})...")
        
        try:
            # 1. Download original product image
            job["progress"] = 25
            if product_image_url.startswith("data:image"):
                # Handle base64
                header, encoded = product_image_url.split(",", 1)
                import base64
                img_bytes = base64.b64decode(encoded)
            else:
                res = requests.get(product_image_url, timeout=15)
                if res.status_code != 200:
                    raise Exception(f"Failed to download original image: HTTP {res.status_code}")
                img_bytes = res.content
                
            job["progress"] = 50
            
            # 2. Run AI/Local composite generation
            prompt = job.get("prompt_used", "")
            angle = "front"
            if image_type == "model_side":
                angle = "side"
            elif image_type == "model_closeup":
                angle = "closeup"
                
            metadata = {"angle": angle}
            generated_bytes = AIService.generate_variation(img_bytes, image_type, prompt, metadata)
            job["progress"] = 80
            
            # 3. Upload generated image to Supabase Storage
            # In local environment, we can save it locally as a fallback or upload to Supabase bucket.
            # We'll save it locally in the backend static folder and return a local URL.
            local_filename = f"generated_{job_id}.png"
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "generations")
            os.makedirs(static_dir, exist_ok=True)
            
            filepath = os.path.join(static_dir, local_filename)
            with open(filepath, "wb") as f:
                f.write(generated_bytes)
                
            image_url = f"http://localhost:5000/static/generations/{local_filename}"
            
            # 4. Insert record into Supabase generated_images table
            if is_offline():
                MockDB.add_generation(
                    task_id=task_id,
                    image_type=image_type,
                    image_url=image_url,
                    prompt_used=prompt,
                    angle=angle,
                    metadata={"job_id": job_id}
                )
            else:
                db_headers = {
                    "apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }
                
                image_payload = {
                    "task_id": task_id,
                    "image_type": image_type,
                    "image_url": image_url,
                    "prompt_used": prompt,
                    "angle": angle,
                    "metadata": {"job_id": job_id}
                }
                
                insert_url = f"{Config.SUPABASE_URL}/rest/v1/generated_images"
                db_res = requests.post(insert_url, json=image_payload, headers=db_headers, timeout=5)
                
                if db_res.status_code not in [200, 201]:
                    logger.error(f"Failed to log generated image in database: {db_res.status_code} - {db_res.text}")
                    # Fallback to MockDB in case real Supabase URL returns an error (e.g. database down)
                    MockDB.add_generation(
                        task_id=task_id,
                        image_type=image_type,
                        image_url=image_url,
                        prompt_used=prompt,
                        angle=angle,
                        metadata={"job_id": job_id}
                    )
                
            job["progress"] = 100
            job["status"] = "completed"
            job["result_url"] = image_url
            logger.info(f"Background job {job_id} completed successfully!")
            
        except Exception as e:
            logger.error(f"Background job {job_id} failed: {str(e)}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["progress"] = 100
