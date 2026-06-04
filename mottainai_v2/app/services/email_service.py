"""
Email service.
Handles all outbound email via SMTP (Gmail App Password or any SMTP provider).
Gracefully no-ops when email is not configured (development mode).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email_service")


def _send_email(to: str, subject: str, body_html: str, body_text: str) -> bool:
    """
    Send a single email via SMTP.
    Returns True on success, False on failure (never raises — email is non-critical).
    """
    if not settings.email_configured:
        logger.warning(
            "Email not configured — skipping send to %s (subject: %s)", to, subject
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.mail_from
        msg["To"] = to

        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.sendmail(settings.mail_from, to, msg.as_string())

        logger.info("Email sent: to=%s subject=%s", to, subject)
        return True

    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


# ---------------------------------------------------------------------------
# Template functions
# ---------------------------------------------------------------------------

def send_verification_email(to: str, full_name: str, token: str) -> bool:
    """Send account verification email."""
    subject = "Verify your Mottainai Smart Pantry account"
    verify_url = f"https://your-domain.com/api/v1/auth/verify-email?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2E7D32;">Welcome to Mottainai Smart Pantry 🥦</h2>
        <p>Hi {full_name},</p>
        <p>Thank you for registering. Please verify your email address to get started.</p>
        <a href="{verify_url}" style="
            display: inline-block;
            background: #2E7D32;
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            margin: 16px 0;
        ">Verify Email</a>
        <p style="color: #666; font-size: 12px;">
            If you did not create this account, please ignore this email.
            This link expires in 24 hours.
        </p>
        <p style="color: #666; font-size: 12px;">
            — The Mottainai Smart Pantry Team
        </p>
    </div>
    """
    text = (
        f"Hi {full_name},\n\n"
        f"Verify your email: {verify_url}\n\n"
        "This link expires in 24 hours.\n"
    )
    return _send_email(to, subject, html, text)


def send_password_reset_email(to: str, full_name: str, token: str) -> bool:
    """Send password reset email."""
    subject = "Reset your Mottainai Smart Pantry password"
    reset_url = f"https://your-domain.com/api/v1/auth/reset-password?token={token}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2E7D32;">Password Reset Request</h2>
        <p>Hi {full_name},</p>
        <p>We received a request to reset your password.</p>
        <a href="{reset_url}" style="
            display: inline-block;
            background: #C62828;
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            margin: 16px 0;
        ">Reset Password</a>
        <p style="color: #666; font-size: 12px;">
            This link expires in 30 minutes.
            If you did not request a reset, please ignore this email.
        </p>
    </div>
    """
    text = (
        f"Hi {full_name},\n\n"
        f"Reset your password: {reset_url}\n\n"
        "This link expires in 30 minutes.\n"
    )
    return _send_email(to, subject, html, text)


def send_expiry_reminder_email(
    to: str,
    full_name: str,
    items: List[dict],  # [{"name": str, "expiry_date": date, "days_left": int}]
) -> bool:
    """Send a single digest email for all expiring items."""
    subject = "🥦 Mottainai: Some pantry items are expiring soon!"

    item_rows = "\n".join(
        f"<tr>"
        f"<td style='padding:8px; border-bottom:1px solid #eee;'>{i['name'].title()}</td>"
        f"<td style='padding:8px; border-bottom:1px solid #eee;'>{i['expiry_date']}</td>"
        f"<td style='padding:8px; border-bottom:1px solid #eee; color:#C62828;'>"
        f"{'Today' if i['days_left'] == 0 else f\"{i['days_left']} day(s)\"}"
        f"</td>"
        f"</tr>"
        for i in items
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2E7D32;">Pantry Expiry Reminder 🥦</h2>
        <p>Hi {full_name},</p>
        <p>The following items in your pantry are expiring soon.
           Use them to reduce food waste!</p>
        <table style="width:100%; border-collapse:collapse; margin:16px 0;">
            <thead>
                <tr style="background:#f5f5f5;">
                    <th style="padding:8px; text-align:left;">Item</th>
                    <th style="padding:8px; text-align:left;">Expires On</th>
                    <th style="padding:8px; text-align:left;">Time Left</th>
                </tr>
            </thead>
            <tbody>{item_rows}</tbody>
        </table>
        <p style="color: #2E7D32; font-style: italic;">
            "Mottainai" — don't let good food go to waste.
        </p>
        <p style="color:#666; font-size:12px;">— Mottainai Smart Pantry</p>
    </div>
    """
    text_items = "\n".join(
        f"- {i['name']} (expires {i['expiry_date']}, {i['days_left']} day(s) left)"
        for i in items
    )
    text = f"Hi {full_name},\n\nExpiring items:\n{text_items}\n\nMottainai Smart Pantry\n"
    return _send_email(to, subject, html, text)
