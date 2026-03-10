"""
Email service — uses Resend API via httpx (avoids Cloudflare 1010 block
that affects raw urllib on Render's IPs).

SETUP:
  1. Sign up at resend.com (free, 100 emails/day)
  2. Get API key from dashboard
  3. Set on Render backend env vars:
       RESEND_API_KEY = re_xxxxxxxxxxxx
       EMAIL_FROM     = onboarding@resend.dev   (no domain verification needed)
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


def _build_html(verify_url: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<body style="font-family: Georgia, serif; background: #f5f2eb; padding: 40px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px;">
    <h1 style="font-size: 22px; color: #1a1a1a; margin: 0 0 16px 0;">Verify your email</h1>
    <p style="color: #555; font-size: 15px; line-height: 1.7; margin: 0 0 24px 0;">
      Welcome to PaperBot. Click the button below to verify your email address.
    </p>
    <a href="{verify_url}" style="display:inline-block;padding:12px 32px;background:#1a1a1a;color:white;text-decoration:none;font-size:14px;letter-spacing:0.5px;">
      Verify Email Address
    </a>
    <p style="color: #999; font-size: 13px; margin: 24px 0 0 0;">
      If you did not create an account, ignore this email.
    </p>
    <p style="color: #bbb; font-size: 12px; margin: 24px 0 0 0; padding-top: 16px; border-top: 1px solid #eee; word-break: break-all;">
      Or copy this link: {verify_url}
    </p>
  </div>
</body>
</html>"""


def _send_via_resend(to_email: str, verify_url: str) -> bool:
    """Send via Resend API using httpx — avoids Cloudflare 1010 block."""
    try:
        import httpx
    except ImportError:
        logger.error("httpx not installed — cannot use Resend API")
        return False

    from_addr = settings.EMAIL_FROM or "onboarding@resend.dev"

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "cie-evaluator/1.0",
            },
            json={
                "from": f"PaperBot <{from_addr}>",
                "to": [to_email],
                "subject": "Verify your PaperBot account",
                "html": _build_html(verify_url),
                "text": f"Verify your email address:\n\n{verify_url}",
            },
            timeout=15,
        )
        if response.status_code in (200, 201):
            logger.info(f"Resend email sent to {to_email}: {response.text}")
            return True
        else:
            logger.error(f"Resend API error {response.status_code} for {to_email}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Resend request failed: {e}")
        return False


def _send_via_smtp(to_email: str, verify_url: str) -> bool:
    """Send via SMTP — works locally, blocked on Render free tier."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your PaperBot account"
    msg["From"] = f"PaperBot <{settings.EMAIL_FROM}>"
    msg["To"] = to_email
    msg.attach(MIMEText(f"Verify your email: {verify_url}", "plain"))
    msg.attach(MIMEText(_build_html(verify_url), "html"))
    try:
        logger.info(f"Connecting to SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT}...")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
        logger.info(f"SMTP email sent to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — use a Gmail App Password, not your account password")
        return False
    except Exception as e:
        logger.error(f"SMTP error: {type(e).__name__}: {e}")
        return False


def send_verification_email(email: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    logger.warning("=" * 60)
    logger.warning(f"VERIFICATION LINK FOR {email}:")
    logger.warning(verify_url)
    logger.warning("=" * 60)

    if settings.RESEND_API_KEY:
        return _send_via_resend(email, verify_url)

    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        return _send_via_smtp(email, verify_url)

    logger.warning("No email provider configured. Copy the link above to verify manually.")
    return True
