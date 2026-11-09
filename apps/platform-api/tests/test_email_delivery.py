from app.core.config import settings
from app.services.email_delivery import send_invitation_email


def test_invitation_email_is_fail_soft_when_smtp_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, 'smtp_host', '')
    monkeypatch.setattr(settings, 'smtp_from_email', '')

    result = send_invitation_email(
        to_email='operator@example.com',
        organization_name='Example Logistics',
        role='operator',
        invite_url='https://console.example.com/accept-invite#token=one-time',
    )

    assert result.sent is False
    assert result.error == 'Email delivery is not configured'


def test_invitation_email_uses_starttls_and_login(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent['connection'] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def starttls(self, context):
            sent['starttls'] = context is not None

        def login(self, username, password):
            sent['login'] = (username, password)

        def send_message(self, message):
            sent['message'] = message

    monkeypatch.setattr(settings, 'smtp_host', 'smtp.example.com')
    monkeypatch.setattr(settings, 'smtp_port', 587)
    monkeypatch.setattr(settings, 'smtp_username', 'mailer')
    monkeypatch.setattr(settings, 'smtp_password', 'secret')
    monkeypatch.setattr(settings, 'smtp_from_email', 'noreply@example.com')
    monkeypatch.setattr(settings, 'smtp_from_name', 'FreightPilot')
    monkeypatch.setattr(settings, 'smtp_use_tls', True)
    monkeypatch.setattr(settings, 'smtp_use_ssl', False)
    monkeypatch.setattr('app.services.email_delivery.smtplib.SMTP', FakeSMTP)

    result = send_invitation_email(
        to_email='operator@example.com',
        organization_name='Example Logistics',
        role='operator',
        invite_url='https://console.example.com/accept-invite#token=one-time',
    )

    assert result.sent is True
    assert result.error is None
    assert sent['connection'] == ('smtp.example.com', 587, 10.0)
    assert sent['starttls'] is True
    assert sent['login'] == ('mailer', 'secret')
    assert sent['message']['To'] == 'operator@example.com'
    plain = sent['message'].get_body(preferencelist=('plain',))
    assert plain is not None
    assert 'one-time' in plain.get_content()
