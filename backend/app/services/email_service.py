"""
Email service — two strategies:
1. Resend HTTPS API  — works on Render free tier (SMTP is blocked)
2. SMTP (Gmail)      — works locally only
Falls back to console logging if neither configured.

RESEND SETUP (free, 100 emails/day):
  1. Sign up at resend.com
  2. Create an API key
  3. Set RESEND_API_KEY env var on Render
  4. Set EMAIL_FROM to: onboarding@resend.dev  (works without domain verification)
     Or verify your own domain and use that.
"""
import logging
import urllib.request
import urllib.error
import json
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
      Welcome to Papers CIE. Click the button below to verify your email address.
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
    """Send via Resend HTTPS API — works on Render free tier."""
    # Use Resend's shared test domain if no custom EMAIL_FROM is set.
    # "onboarding@resend.dev" works without domain verification but
    # can only send to the account owner's email on the free plan.
    from_addr = settings.EMAIL_FROM or "onboarding@resend.dev"
    from_label = f"Papers CIE <{from_addr}>"

    payload = json.dumps({
        "from": from_label,
        "to": [to_email],
        "subject": "Verify your Papers CIE account",
        "html": _build_html(verify_url),
        "text": f"Verify your email address:\n\n{verify_url}",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            logger.info(f"Resend API success for {to_email}: {body}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        logger.error(f"Resend API HTTP {e.code} for {to_email}: {body}")
        return False
    except Exception as e:
        logger.error(f"Resend request failed: {e}")
        return False


def _send_via_smtp(to_email: str, verify_url: str) -> bool:
    """Send via SMTP — works locally, blocked on Render free tier."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your Papers CIE account"
    msg["From"] = f"Papers CIE <{settings.EMAIL_FROM}>"
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

    # Always log the URL so you can verify manually if email fails
    logger.warning("=" * 60)
    logger.warning(f"VERIFICATION LINK FOR {email}:")
    logger.warning(verify_url)
    logger.warning("=" * 60)

    # Strategy 1: Resend API (use on Render — SMTP is blocked there)
    if settings.RESEND_API_KEY:
        return _send_via_resend(email, verify_url)

    # Strategy 2: SMTP (use locally)
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        return _send_via_smtp(email, verify_url)

    # Strategy 3: Console only — link is in logs above
    logger.warning("No email provider configured. Copy the link above to verify.")
    return True
