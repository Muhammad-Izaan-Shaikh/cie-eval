import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging
import socket


logger = logging.getLogger(__name__)


def send_verification_email(email: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    # Always log to console so dev mode always works
    logger.warning("=" * 60)
    logger.warning(f"VERIFICATION LINK FOR {email}:")
    logger.warning(verify_url)
    logger.warning("=" * 60)

    # If SMTP not configured, skip sending but don't fail
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured. Email not sent. Use the URL above to verify.")
        return True  # Return True so registration still succeeds

    html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: Georgia, serif; background: #f5f2eb; padding: 40px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px;">
    <h1 style="font-size: 22px; color: #1a1a1a; margin: 0 0 16px 0;">Verify your email</h1>
    <p style="color: #555; font-size: 15px; line-height: 1.7; margin: 0 0 24px 0;">
      Welcome to CIE Evaluator. Click the button below to verify your email address and activate your account.
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your CIE Evaluator account"
    msg["From"] = f"CIE Evaluator <{settings.EMAIL_FROM}>"
    msg["To"] = email
    msg.attach(MIMEText(f"Verify your email: {verify_url}", "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        logger.info(f"Connecting to SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT}...")
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.set_debuglevel(1)   # logs SMTP conversation to console
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [email], msg.as_string())
        logger.info(f"✓ Verification email sent successfully to {email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        logger.error("Check your SMTP_USER and SMTP_PASSWORD in .env")
        logger.error("For Gmail: use an App Password, not your regular password")
        return False

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {email}: {e}")
        return False

    except socket.timeout:
        logger.error(f"SMTP connection timed out to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error sending email to {email}: {type(e).__name__}: {e}")
        return False
