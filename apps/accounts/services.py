"""Helpers for per-user settings, sending e-mail from the user's own mailbox, WhatsApp links and public URLs."""
import re
import smtplib
import socket
import urllib.parse
from email.utils import formataddr

from django.core.mail import EmailMessage, get_connection
from django.urls import reverse

from .models import UserSettings


class MailerError(Exception):
    """Raised with a message that is safe to show to the user."""


def get_user_settings(user):
    obj, _ = UserSettings.objects.get_or_create(user=user)
    return obj


# --------------------------------------------------------------------------
# Public links (what the CLIENT opens)
# --------------------------------------------------------------------------
def public_url(request, user, path):
    base = (get_user_settings(user).public_base_url or "").rstrip("/")
    return f"{base}{path}" if base else request.build_absolute_uri(path)


def is_local_link(request, user):
    """True when links we generate would point at this computer (clients can't open those)."""
    if get_user_settings(user).public_base_url:
        return False
    host = request.get_host().split(":")[0]
    return host in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]") or host.startswith(("192.168.", "10."))


def portfolio_link(request, user, workspace):
    """Public portfolio URL, or '' when disabled / nothing published yet."""
    s = get_user_settings(user)
    if not s.portfolio_enabled or not workspace:
        return ""
    if not workspace.portfolio_items.filter(is_published=True).exists():
        return ""
    return public_url(request, user, reverse("public_portfolio", args=[workspace.slug]))


# --------------------------------------------------------------------------
# WhatsApp (opens the user's own WhatsApp with the message pre-filled)
# --------------------------------------------------------------------------
def clean_whatsapp_number(phone, default_country_code=""):
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0") and default_country_code:
        digits = re.sub(r"\D", "", default_country_code) + digits[1:]
    return digits


def whatsapp_link(number, text=""):
    digits = re.sub(r"\D", "", number or "")
    if not digits:
        return ""
    url = f"https://wa.me/{digits}"
    return f"{url}?text={urllib.parse.quote(text)}" if text else url


# --------------------------------------------------------------------------
# E-mail from the user's own mailbox
# --------------------------------------------------------------------------
def _connection(s):
    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=s.smtp_host,
        port=s.smtp_port,
        username=s.smtp_username,
        password=s.smtp_password,
        use_tls=(s.smtp_security == "TLS"),
        use_ssl=(s.smtp_security == "SSL"),
        timeout=20,
        fail_silently=False,
    )


def _from_header(user, s):
    address = s.from_email or (s.smtp_username if "@" in s.smtp_username else user.email)
    name = s.from_name or user.full_name
    return formataddr((name, address)) if name else address


def _explain(exc):
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return ("Your mail provider rejected the username/password. For Gmail or Outlook with 2-step verification "
                "you must create an 'App Password' and use that instead of your normal password.")
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return "The recipient address was refused by the mail server. Check the client's email address."
    if isinstance(exc, smtplib.SMTPSenderRefused):
        return "Your mail provider refused the sender address. Set 'Sender email' to your own mailbox address in Settings."
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "Connecting to your mail server timed out. Check the SMTP host, port and security type."
    if isinstance(exc, (socket.gaierror, ConnectionRefusedError)):
        return "Could not reach your mail server. Check the SMTP host and port."
    return f"Sending failed: {exc}"


def send_user_email(user, to_email, subject, body):
    """Send from the user's own SMTP mailbox. Raises MailerError (never pretends it worked)."""
    s = get_user_settings(user)
    if not s.smtp_ready:
        raise MailerError("Email is not set up yet. Open Settings > Email and add your SMTP details first.")
    message = EmailMessage(
        subject=subject,
        body=body,
        from_email=_from_header(user, s),
        to=[to_email],
        reply_to=[s.reply_to or user.email],
        connection=_connection(s),
    )
    try:
        message.send(fail_silently=False)
    except Exception as exc:  # smtplib / socket / ssl errors
        raise MailerError(_explain(exc)) from exc


def compose_message(user, body, portfolio_url=""):
    """Add portfolio link, signature and opt-out line to an outgoing email body."""
    s = get_user_settings(user)
    parts = [body.rstrip()]
    if portfolio_url:
        parts.append(f"You can see some of my recent live projects here:\n{portfolio_url}")
    if s.email_signature.strip():
        parts.append(s.email_signature.strip())
    if s.email_footer.strip():
        parts.append(f"--\n{s.email_footer.strip()}")
    return "\n\n".join(parts)
