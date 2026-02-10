from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import settings


class EmailService:
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.EMAIL_FROM
        self.enabled = bool(self.api_key)

        if self.enabled:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            print("⚠️ Email service disabled (no SENDGRID_API_KEY)")

    def send_email(self, to_email: str, subject: str, html_content: str):
        if not self.enabled:
            print(f"[EMAIL DISABLED] To: {to_email} | Subject: {subject}")
            return

        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )

        try:
            self.client.send(message)
        except Exception as e:
            print(f"Email send failed: {e}")


email_service = EmailService()
