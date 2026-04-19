import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re
from typing import Dict

load_dotenv()


class EmailService:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASS")
        self.from_email = os.getenv("FROM_EMAIL", self.user)

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        text = re.sub(r'<p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        return text.strip()

    async def send_single(self, to_email: str, subject: str, html_body: str, body: str = None) -> Dict:
        """Send single email."""
        try:
            rendered_body = body if body else self._html_to_text(html_body)

            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(rendered_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                start_tls=True,
                validate_certs=False,
                username=self.user,
                password=self.password,
            )
            return {"email": to_email, "status": "sent", "error": None}
        except Exception as e:
            print(f"EMAIL ERROR: {e}")
            return {"email": to_email, "status": "failed", "error": str(e)}

