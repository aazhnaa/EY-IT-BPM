import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class NotificationAgent:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")

    def send_email(self, recipient, subject, html_body):
        """
        Sends a real HTML email using Gmail SMTP.
        """
        print(f"📧 [NotificationAgent] Sending email to {recipient}...")
        
        if not self.sender_email or not self.password:
            return {"status": "error", "message": "Email credentials missing in .env"}

        try:
            # Create Message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient

            # Attach HTML Body
            msg.attach(MIMEText(html_body, "html"))

            # Send via Gmail SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls() # Secure connection
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
            
            print("✅ [NotificationAgent] Email sent successfully!")
            return {"status": "success", "message": "Email sent"}

        except Exception as e:
            print(f"❌ [NotificationAgent] Failed to send: {e}")
            return {"status": "error", "message": str(e)}