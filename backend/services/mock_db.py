import uuid
import datetime
import threading

class MockDB:
    _lock = threading.Lock()
    
    # Pre-populated default task ID for immediate developer experience
    DEFAULT_TASK_ID = "c0de1234-abcd-1234-5678-000000000000"
    
    # In-memory mock tables
    tasks = [
        {
            "id": DEFAULT_TASK_ID,
            "title": "Default Pearl Necklace Shoot",
            "description": "Generate 8 DSLR-quality variations for the default pearl necklace.",
            "status": "assigned",
            "product_image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&q=80&w=600",
            "assigned_to": "mock-user-id",
            "created_by": "mock-admin-id",
            "revision_notes": None,
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z",
            "updated_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z",
            "assigned_to_details": {
                "email": "user@taskhub.dev",
                "full_name": "Demo Photographer User"
            }
        }
    ]
    
    generated_images = []
    audit_logs = [
        {
            "id": "1",
            "table_name": "tasks",
            "action": "CREATE",
            "row_id": DEFAULT_TASK_ID,
            "performed_by": "mock-admin-id",
            "old_data": None,
            "new_data": {
                "id": DEFAULT_TASK_ID,
                "title": "Default Pearl Necklace Shoot",
                "status": "assigned"
            },
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z"
        }
    ]

    @classmethod
    def get_all_tasks(cls):
        with cls._lock:
            # We must return details with user info attached
            result = []
            for task in cls.tasks:
                t = task.copy()
                if t.get("assigned_to") == "mock-user-id":
                    t["assigned_to"] = {
                        "email": "user@taskhub.dev",
                        "full_name": "Demo Photographer User"
                    }
                elif t.get("assigned_to") == "mock-admin-id":
                    t["assigned_to"] = {
                        "email": "admin@taskhub.dev",
                        "full_name": "Demo Administrator"
                    }
                result.append(t)
            return result

    @classmethod
    def get_my_tasks(cls, user_id):
        with cls._lock:
            return [task.copy() for task in cls.tasks if task.get("assigned_to") == user_id]

    @classmethod
    def get_task(cls, task_id):
        with cls._lock:
            for task in cls.tasks:
                if task["id"] == str(task_id):
                    return task.copy()
            return None

    @classmethod
    def create_task(cls, title, description, product_image_url, created_by, assigned_to=None):
        with cls._lock:
            task_id = str(uuid.uuid4())
            now = datetime.datetime.utcnow().isoformat() + "Z"
            
            task = {
                "id": task_id,
                "title": title,
                "description": description,
                "product_image_url": product_image_url,
                "status": "assigned" if assigned_to else "pending",
                "assigned_to": assigned_to,
                "created_by": created_by,
                "revision_notes": None,
                "created_at": now,
                "updated_at": now,
                "assigned_to_details": {
                    "email": "user@taskhub.dev" if assigned_to == "mock-user-id" else "unknown@taskhub.dev",
                    "full_name": "Demo Photographer User" if assigned_to == "mock-user-id" else "Unknown User"
                } if assigned_to else None
            }
            cls.tasks.append(task)
            cls.log_audit("tasks", "CREATE", task_id, None, task, created_by)
            return task.copy()

    @classmethod
    def update_task_status(cls, task_id, status, performed_by, revision_notes=None):
        with cls._lock:
            for task in cls.tasks:
                if task["id"] == str(task_id):
                    old_task = task.copy()
                    task["status"] = status
                    task["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                    if revision_notes is not None:
                        task["revision_notes"] = revision_notes
                    
                    cls.log_audit("tasks", "UPDATE", task_id, old_task, task, performed_by)
                    return task.copy()
            return None

    @classmethod
    def assign_task(cls, task_id, assigned_to, performed_by):
        with cls._lock:
            for task in cls.tasks:
                if task["id"] == str(task_id):
                    old_task = task.copy()
                    task["assigned_to"] = assigned_to
                    task["status"] = "assigned"
                    task["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                    task["assigned_to_details"] = {
                        "email": "user@taskhub.dev" if assigned_to == "mock-user-id" else "unknown@taskhub.dev",
                        "full_name": "Demo Photographer User" if assigned_to == "mock-user-id" else "Unknown User"
                    }
                    cls.log_audit("tasks", "UPDATE", task_id, old_task, task, performed_by)
                    return task.copy()
            return None

    @classmethod
    def delete_task(cls, task_id, performed_by):
        with cls._lock:
            for i, task in enumerate(cls.tasks):
                if task["id"] == str(task_id):
                    old_task = task.copy()
                    del cls.tasks[i]
                    cls.log_audit("tasks", "DELETE", task_id, old_task, None, performed_by)
                    return True
            return False

    @classmethod
    def get_task_generations(cls, task_id):
        with cls._lock:
            return [img.copy() for img in cls.generated_images if img.get("task_id") == str(task_id)]

    @classmethod
    def add_generation(cls, task_id, image_type, image_url, prompt_used, angle, metadata=None):
        with cls._lock:
            gen_id = str(uuid.uuid4())
            now = datetime.datetime.utcnow().isoformat() + "Z"
            gen = {
                "id": gen_id,
                "task_id": str(task_id),
                "image_type": image_type,
                "image_url": image_url,
                "prompt_used": prompt_used,
                "angle": angle,
                "metadata": metadata or {},
                "created_at": now
            }
            cls.generated_images.append(gen)
            # Find the user assigned to this task for audit trail
            assigned_user = "system"
            for t in cls.tasks:
                if t["id"] == str(task_id):
                    assigned_user = t.get("assigned_to", "system")
                    break
            cls.log_audit("generated_images", "CREATE", gen_id, None, gen, performed_by=assigned_user)
            return gen.copy()

    @classmethod
    def delete_generation(cls, gen_id, performed_by):
        with cls._lock:
            for i, img in enumerate(cls.generated_images):
                if img["id"] == str(gen_id):
                    old_img = img.copy()
                    del cls.generated_images[i]
                    cls.log_audit("generated_images", "DELETE", gen_id, old_img, None, performed_by)
                    return old_img
            return None

    @classmethod
    def get_audit_logs(cls):
        with cls._lock:
            return [log.copy() for log in cls.audit_logs]

    @classmethod
    def log_audit(cls, table_name, action, row_id, old_data=None, new_data=None, performed_by="system"):
        # This method assumes it's called inside an active lock if called internally
        log_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat() + "Z"
        log = {
            "id": log_id,
            "table_name": table_name,
            "action": action,
            "row_id": str(row_id),
            "performed_by": performed_by or "system",
            "old_data": old_data,
            "new_data": new_data,
            "created_at": now
        }
        cls.audit_logs.append(log)
        # Keep logs list bounded
        if len(cls.audit_logs) > 100:
            cls.audit_logs.pop(0)
