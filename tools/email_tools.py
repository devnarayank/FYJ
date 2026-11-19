"""
Email tools — SMTP sending and IMAP inbox monitoring.
"""
import email
import imaplib
import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from config.constants import EMAIL_DELAY_SECONDS
from tools.validators import validate_email_address, validate_port_number

logger = logging.getLogger(__name__)


# ── SMTP Sending ──

def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    from_name: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    reply_to: str | None = None,
) -> dict:
    """
    Send an email via SMTP_SSL.
    Returns {"success": bool, "message_id": str, "error": str | None}
    """
    try:
        # Validate all email addresses
        try:
            from_email = validate_email_address(from_email)
            to_email = validate_email_address(to_email)
            if reply_to:
                reply_to = validate_email_address(reply_to)
        except ValueError as e:
            logger.error(f"Email validation failed: {e}")
            return {"success": False, "message_id": "", "error": f"Invalid email format: {str(e)}"}

        # Validate SMTP port
        try:
            smtp_port = validate_port_number(smtp_port)
        except ValueError as e:
            logger.error(f"Invalid SMTP port: {e}")
            return {"success": False, "message_id": "", "error": f"Invalid SMTP port: {str(e)}"}

        # Validate credentials exist
        if not smtp_user or not smtp_pass:
            logger.error("SMTP credentials missing")
            return {"success": False, "message_id": "", "error": "SMTP credentials missing"}

        # Validate subject and body
        if not subject or not subject.strip():
            logger.error("Email subject cannot be empty")
            return {"success": False, "message_id": "", "error": "Email subject cannot be empty"}

        if not body or not body.strip():
            logger.error("Email body cannot be empty")
            return {"success": False, "message_id": "", "error": "Email body cannot be empty"}

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=from_email.split("@")[1])
        if reply_to:
            msg["Reply-To"] = reply_to

        # Plain text version
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # HTML version (simple formatting)
        html_body = body.replace("\n\n", "</p><p>").replace("\n", "<br>")
        html_body = f"<html><body><p>{html_body}</p></body></html>"
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Use SSL context for secure connection with certificate verification
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with smtplib.SMTP_SSL(
            smtp_host, smtp_port, timeout=30, context=context
        ) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        message_id = msg["Message-ID"]
        logger.info(f"Email sent to {to_email}: {subject} (ID: {message_id})")
        return {"success": True, "message_id": message_id, "error": None}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth failed: {e}")
        return {"success": False, "message_id": "", "error": f"Authentication failed: {e}"}
    except ssl.SSLError as e:
        logger.error(f"SSL/TLS connection failed: {e}")
        return {"success": False, "message_id": "", "error": f"SSL/TLS error: {e}"}
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return {"success": False, "message_id": "", "error": str(e)}


def send_email_with_rate_limit(
    smtp_config: dict,
    to_email: str,
    subject: str,
    body: str,
) -> dict:
    """Send email with built-in rate limiting delay."""
    result = send_email(
        smtp_host=smtp_config["host"],
        smtp_port=smtp_config["port"],
        smtp_user=smtp_config["username"],
        smtp_pass=smtp_config["password"],
        from_name=smtp_config["from_name"],
        from_email=smtp_config["from_email"],
        to_email=to_email,
        subject=subject,
        body=body,
    )
    # Rate limit: wait between sends
    time.sleep(EMAIL_DELAY_SECONDS)
    return result


# ── IMAP Reading ──

def check_inbox(
    imap_host: str,
    imap_port: int,
    imap_user: str,
    imap_pass: str,
    since_date: str | None = None,
    unseen_only: bool = True,
) -> list[dict]:
    """
    Check inbox for new emails.
    Returns list of dicts with: from, subject, body, date, message_id
    """
    emails_found = []

    try:
        with imaplib.IMAP4_SSL(imap_host, imap_port) as mail:
            mail.login(imap_user, imap_pass)
            mail.select("INBOX")

            # Build search criteria
            criteria = "(UNSEEN)" if unseen_only else "ALL"
            if since_date:
                criteria = f'(SINCE "{since_date}" UNSEEN)' if unseen_only else f'(SINCE "{since_date}")'

            status, data = mail.search(None, criteria)
            if status != "OK" or not data[0]:
                return []

            email_ids = data[0].split()
            logger.info(f"Found {len(email_ids)} emails matching criteria")

            for eid in email_ids[-50:]:  # Limit to last 50
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                            except Exception:
                                body = str(part.get_payload())
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        body = str(msg.get_payload())

                from_addr = email.utils.parseaddr(msg.get("From", ""))[1]

                emails_found.append({
                    "from": from_addr,
                    "subject": str(msg.get("Subject", "")),
                    "body": body[:2000],  # Truncate for safety
                    "date": str(msg.get("Date", "")),
                    "message_id": str(msg.get("Message-ID", "")),
                    "in_reply_to": str(msg.get("In-Reply-To", "")),
                })

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error: {e}")
    except Exception as e:
        logger.error(f"Inbox check failed: {e}")

    return emails_found
