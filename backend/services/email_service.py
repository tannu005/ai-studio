import logging
import requests
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_service")

class EmailService:
    @staticmethod
    def _send_email(to_email, subject, html_content):
        """Dispatches email via Resend or logs it locally if no key is configured"""
        if not Config.RESEND_API_KEY:
            logger.info("=========================================")
            logger.info("MOCK EMAIL SENT (No Resend API Key)")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content Preview: {html_content[:300]}...")
            logger.info("=========================================")
            return True
            
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": Config.FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 201]:
                logger.info(f"Email sent successfully to {to_email} via Resend")
                return True
            else:
                logger.error(f"Failed to send email via Resend: {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Email service exception: {str(e)}")
            return False

    @classmethod
    def send_task_assigned(cls, user_email, user_name, task_title, task_id, preview_image_url):
        """Notify User when a task is assigned to them"""
        subject = f"New Task Assigned: {task_title}"
        task_link = f"http://localhost:3000/tasks/{task_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Task Assigned</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(30, 41, 59, 0.7); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); }}
                .header {{ border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 20px; margin-bottom: 20px; }}
                .logo {{ font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .title {{ font-size: 20px; margin-top: 10px; color: #f8fafc; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #cbd5e1; }}
                .task-card {{ background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                .task-card img {{ max-width: 100%; height: 200px; object-fit: contain; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.1); margin-top: 10px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #6366f1, #4f46e5); color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 10px rgba(99, 102, 241, 0.4); }}
                .footer {{ font-size: 12px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo">TaskHub</span>
                    <h2 class="title">New Task Assigned</h2>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>You have been assigned a new product photography task on TaskHub. Please review the details below and open the AI Studio to begin generating the variations.</p>
                    
                    <div class="task-card">
                        <strong style="color: #f8fafc; font-size: 18px;">{task_title}</strong>
                        <br/>
                        <img src="{preview_image_url}" alt="Product Preview" />
                    </div>
                    
                    <p>You are required to generate <strong>8 consistent product variations</strong> (1 white background, 2 themed backgrounds, 2 creative backgrounds, and 3 model wearing angles) while ensuring the product itself remains exactly identical.</p>
                    
                    <div style="text-align: center;">
                        <a href="{task_link}" class="btn">Open AI Studio</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message from TaskHub. Please do not reply directly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return cls._send_email(user_email, subject, html_content)

    @classmethod
    def send_task_submitted(cls, admin_email, user_name, task_title, task_id, total_images=8):
        """Notify Admin when a user submits their task"""
        subject = f"Task Completed: {task_title} by {user_name}"
        review_link = f"http://localhost:3000/tasks/{task_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Task Submitted for Review</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(30, 41, 59, 0.7); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); }}
                .header {{ border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 20px; margin-bottom: 20px; }}
                .logo {{ font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .title {{ font-size: 20px; margin-top: 10px; color: #f8fafc; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #cbd5e1; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #10b981, #059669); color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.4); }}
                .footer {{ font-size: 12px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo">TaskHub</span>
                    <h2 class="title">Task Submitted for Review</h2>
                </div>
                <div class="content">
                    <p>Hello Admin,</p>
                    <p>The user <strong>{user_name}</strong> has completed and submitted the task <strong>{task_title}</strong>.</p>
                    <p>All <strong>{total_images} product variations</strong> have been successfully generated and marked as finalized.</p>
                    
                    <p>Please review the submitted images using the link below to accept the completion or request a revision.</p>
                    
                    <div style="text-align: center;">
                        <a href="{review_link}" class="btn">Review Submissions</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message from TaskHub. Please do not reply directly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return cls._send_email(admin_email, subject, html_content)

    @classmethod
    def send_task_status_update(cls, user_email, user_name, task_title, task_id, status, feedback=""):
        """Notify User when Admin accepts or requests revision for a task"""
        is_accepted = status == "accepted"
        status_text = "Accepted" if is_accepted else "Revision Requested"
        subject = f"Task Accepted: {task_title}" if is_accepted else f"Task Revision Requested: {task_title}"
        task_link = f"http://localhost:3000/tasks/{task_id}"
        
        btn_color = "linear-gradient(135deg, #10b981, #059669)" if is_accepted else "linear-gradient(135deg, #f59e0b, #d97706)"
        btn_text = "View Task" if is_accepted else "Revise Generations"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Task {status_text}</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(30, 41, 59, 0.7); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 40px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5); }}
                .header {{ border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 20px; margin-bottom: 20px; }}
                .logo {{ font-size: 24px; font-weight: bold; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .title {{ font-size: 20px; margin-top: 10px; color: #f8fafc; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #cbd5e1; }}
                .feedback-box {{ background: rgba(30, 41, 59, 0.9); border-left: 4px solid {'#10b981' if is_accepted else '#f59e0b'}; border-radius: 4px; padding: 15px; margin: 20px 0; color: #e2e8f0; font-style: italic; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: {btn_color}; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; }}
                .footer {{ font-size: 12px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo">TaskHub</span>
                    <h2 class="title">Task {status_text}</h2>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    <p>Your submitted task <strong>{task_title}</strong> has been reviewed by the administrator.</p>
                    
                    <p>Status: <strong style="color: {'#10b981' if is_accepted else '#f59e0b'};">{status_text.upper()}</strong></p>
                    
                    {f'<div class="feedback-box"><strong>Feedback:</strong><br/>{feedback}</div>' if feedback else ''}
                    
                    <div style="text-align: center;">
                        <a href="{task_link}" class="btn">{btn_text}</a>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message from TaskHub. Please do not reply directly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return cls._send_email(user_email, subject, html_content)
