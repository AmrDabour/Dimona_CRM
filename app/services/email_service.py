"""Transactional email via SMTP (e.g. Gmail + App Password). Used from Celery workers."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_password() -> str:
    return (settings.smtp_password or "").replace(" ", "")


def _from_tuple() -> tuple[str, str]:
    name = settings.smtp_from_name or settings.app_name
    addr = (settings.smtp_from_email or settings.smtp_user or "").strip()
    return name, addr


def send_email_sync(
    to_addresses: list[str],
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> bool:
    """
    Send email synchronously. Safe no-op when SMTP is disabled or misconfigured.
    Returns True if sent, False if skipped or failed (errors are logged).
    """
    if not settings.smtp_enabled:
        logger.warning(
            "Transactional email skipped: SMTP_ENABLED is false (set true in env for api/celery-worker). "
            "Recipients would have been: %s",
            to_addresses,
        )
        return False

    recipients = [e.strip() for e in to_addresses if e and e.strip()]
    if not recipients:
        logger.warning("send_email_sync: no valid recipients")
        return False

    user = (settings.smtp_user or "").strip()
    password = _smtp_password()
    from_name, from_email = _from_tuple()
    if not user or not password or not from_email:
        logger.warning(
            "SMTP enabled but credentials incomplete: need smtp_user, smtp_password, and smtp_from_email "
            "(or smtp_user as from). Skip send to %s",
            to_addresses,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(from_email, recipients, msg.as_string())
        logger.info("Sent email to %s subject=%s", recipients, subject[:80])
        return True
    except Exception:
        logger.exception("SMTP send failed to %s", recipients)
        return False
