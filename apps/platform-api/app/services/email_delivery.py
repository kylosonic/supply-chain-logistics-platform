"""Optional SMTP delivery for workspace invitations.

SMTP is intentionally optional: an unconfigured deployment keeps the secure
copyable invitation URL and reports that email was not sent. Configuration is
read from the deployment environment; credentials never enter audit payloads.
"""

from __future__ import annotations

import html
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings

_ERROR_MAX_CHARS = 200


@dataclass(frozen=True)
class EmailDeliveryResult:
    sent: bool
    error: str | None = None


def _smtp_connection() -> smtplib.SMTP:
    if settings.smtp_use_ssl:
        return smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
            context=ssl.create_default_context(),
        )
    return smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=settings.smtp_timeout_seconds,
    )


def send_invitation_email(
    *,
    to_email: str,
    organization_name: str,
    role: str,
    invite_url: str,
) -> EmailDeliveryResult:
    if not settings.smtp_host or not settings.smtp_from_email:
        return EmailDeliveryResult(False, 'Email delivery is not configured')

    subject = f'You were invited to {organization_name} on FreightPilot'
    text = (
        f'{organization_name} invited you to join their FreightPilot workspace '
        f'as {role}.\n\n'
        f'Accept the invitation: {invite_url}\n\n'
        'This link expires in 72 hours. If you were not expecting it, ignore this email.'
    )
    html_body = (
        f'<p>{html.escape(organization_name)} invited you to join their FreightPilot '
        f'workspace as <strong>{html.escape(role)}</strong>.</p>'
        f'<p><a href="{html.escape(invite_url, quote=True)}">Accept the invitation</a></p>'
        '<p>This link expires in 72 hours. If you were not expecting it, ignore this email.</p>'
    )
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = f'{settings.smtp_from_name} <{settings.smtp_from_email}>'
    message['To'] = to_email
    message.set_content(text)
    message.add_alternative(html_body, subtype='html')

    try:
        with _smtp_connection() as smtp:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001 - invite creation must still succeed
        return EmailDeliveryResult(
            False,
            f'Email delivery failed: {str(exc)[:_ERROR_MAX_CHARS]}',
        )
    return EmailDeliveryResult(True)
