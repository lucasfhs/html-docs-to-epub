"""Send EPUB files to Kindle via email."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from .progress import show_error, show_info, show_success

logger = logging.getLogger(__name__)

# SMTP servers for common email providers
SMTP_SERVERS: dict[str, tuple[str, int]] = {
    "gmail": ("smtp.gmail.com", 587),
    "outlook": ("smtp.office365.com", 587),
    "hotmail": ("smtp.office365.com", 587),
    "yahoo": ("smtp.mail.yahoo.com", 587),
    "icloud": ("smtp.mail.me.com", 587),
}


def detect_smtp_server(email: str) -> tuple[str, int]:
    """Detect SMTP server from email address."""
    domain = email.split("@")[-1].lower()
    for provider, server in SMTP_SERVERS.items():
        if provider in domain:
            return server
    # Fallback: try common SMTP port with generic server
    return (f"smtp.{domain}", 587)


def send_to_kindle(
    epub_path: Path,
    kindle_email: str,
    sender_email: str,
    sender_password: str,
    smtp_server: str = "",
    smtp_port: int = 587,
    use_tls: bool = True,
) -> bool:
    """Send an EPUB file to a Kindle email address.

    Args:
        epub_path: Path to the EPUB file.
        kindle_email: Destination Kindle email address.
        sender_email: Sender email address (must have SMTP access).
        sender_password: Sender email password or app password.
        smtp_server: SMTP server address (auto-detected if empty).
        smtp_port: SMTP server port (default: 587).
        use_tls: Whether to use TLS encryption (default: True).

    Returns:
        True if sent successfully, False otherwise.
    """
    if not epub_path.exists():
        show_error(f"EPUB file not found: {epub_path}")
        return False

    # Auto-detect SMTP server if not provided
    if not smtp_server:
        smtp_server, default_port = detect_smtp_server(sender_email)
        if smtp_port == 587:
            smtp_port = default_port
        show_info(f"Using SMTP server: {smtp_server}:{smtp_port}")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = kindle_email
    msg["Subject"] = epub_path.stem

    # Body text (Kindle ignores this but some providers require it)
    body = MIMEText(f"Sending {epub_path.name} to Kindle.", "plain", "utf-8")
    msg.attach(body)

    # Attach EPUB file
    with open(epub_path, "rb") as f:
        part = MIMEBase("application", "epub+zip")
        part.set_payload(f.read())

    from email import encoders

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{epub_path.name}"',
    )
    msg.attach(part)

    try:
        show_info(f"Connecting to {smtp_server}:{smtp_port}...")
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=context)
                server.ehlo()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        show_success(f"EPUB sent to {kindle_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        show_error(
            "Authentication failed. Check your email/password.\n"
            "  For Gmail, use an App Password: https://myaccount.google.com/apppasswords"
        )
        return False
    except smtplib.SMTPConnectError as e:
        show_error(f"Could not connect to SMTP server: {e}")
        return False
    except smtplib.SMTPException as e:
        show_error(f"SMTP error: {e}")
        return False
    except TimeoutError:
        show_error("Connection timed out. Check your network and SMTP settings.")
        return False
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")
        show_error(f"Failed to send email: {e}")
        return False
