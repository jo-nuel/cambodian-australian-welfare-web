from django.conf import settings
from django.core.mail import send_mail


def _newsletter_base_url():
    return getattr(settings, 'NEWSLETTER_CONFIRM_URL_BASE', 'http://localhost:8000').rstrip('/')


def send_confirmation_email(subscriber):
    """Send a double opt-in confirmation email. Raises on failure; callers must handle."""
    confirm_url = f'{_newsletter_base_url()}/newsletter/confirm/{subscriber.confirm_token}/'
    send_mail(
        subject='Confirm your CAWC newsletter subscription',
        message=(
            'Hi,\n\n'
            'Thank you for subscribing to the CAWC NSW newsletter.\n\n'
            'Please confirm your email address by clicking the link below:\n\n'
            f'{confirm_url}\n\n'
            'This link expires in 48 hours. If you did not sign up, you can ignore this email.\n\n'
            '- CAWC NSW'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[subscriber.email],
        fail_silently=False,
    )


def send_welcome_email(subscriber):
    """Send a short welcome email after a subscriber confirms."""
    unsubscribe_url = f'{_newsletter_base_url()}/newsletter/unsubscribe/{subscriber.unsubscribe_token}/'
    send_mail(
        subject='Welcome to CAWC NSW updates',
        message=(
            'Hi,\n\n'
            'Thank you for confirming your CAWC NSW newsletter subscription.\n\n'
            'We will send occasional community news, program updates, events, and ways to get involved.\n\n'
            f'You can unsubscribe any time using this link:\n{unsubscribe_url}\n\n'
            '- CAWC NSW'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[subscriber.email],
        fail_silently=False,
    )
