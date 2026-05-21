import logging
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .email import send_confirmation_email, send_welcome_email
from .forms import SubscriptionForm
from .models import Subscriber, _default_token, _default_token_expiry

logger = logging.getLogger(__name__)


@require_POST
def subscribe(request):
    form = SubscriptionForm(request.POST)
    if not form.is_valid():
        referer = request.META.get('HTTP_REFERER', '/')
        parsed = urlparse(referer)
        # Only redirect back to the referer if it is on our own host.
        # Falls back to '/' for any external or malformed referer.
        safe_referer = referer if parsed.netloc in settings.ALLOWED_HOSTS or not parsed.netloc else '/'
        return redirect(f'{safe_referer}?subscribe_error=1')

    email = form.cleaned_data['email']
    language = form.cleaned_data.get('language_preference', Subscriber.LANGUAGE_ANY)
    source = request.POST.get('source', 'footer')

    try:
        subscriber = Subscriber.objects.get(email=email)
    except Subscriber.DoesNotExist:
        subscriber = None

    if subscriber:
        if subscriber.status == Subscriber.STATUS_CONFIRMED:
            return redirect('newsletter_already_subscribed')
        # Pending or unsubscribed — refresh token and resend
        subscriber.status = Subscriber.STATUS_PENDING
        subscriber.confirm_token = _default_token()
        subscriber.token_expires_at = _default_token_expiry()
        subscriber.language_preference = language
        subscriber.source = source
        subscriber.unsubscribed_at = None
        subscriber.confirmed_at = None
        subscriber.save()
    else:
        subscriber = Subscriber.objects.create(
            email=email,
            language_preference=language,
            source=source,
        )

    try:
        send_confirmation_email(subscriber)
    except Exception:
        logger.exception('Failed to send confirmation email to %s', subscriber.email)
        return redirect(f'{reverse("newsletter_check_email")}?status=delivery_issue')

    return redirect('newsletter_check_email')


def check_email(request):
    return render(request, 'a_subscribers/check_email.html', {
        'delivery_issue': request.GET.get('status') == 'delivery_issue',
    })


def confirm(request, token):
    try:
        subscriber = Subscriber.objects.get(confirm_token=token)
    except Subscriber.DoesNotExist:
        return render(request, 'a_subscribers/token_expired.html', status=404)

    if subscriber.status == Subscriber.STATUS_CONFIRMED:
        return redirect('newsletter_confirmed')

    if not subscriber.is_token_valid():
        return render(request, 'a_subscribers/token_expired.html', status=410)

    subscriber.confirm()
    try:
        send_welcome_email(subscriber)
    except Exception:
        logger.exception('Failed to send welcome email to %s', subscriber.email)
    return redirect('newsletter_confirmed')


def confirmed(request):
    return render(request, 'a_subscribers/confirmed.html')


def unsubscribe(request, token):
    try:
        subscriber = Subscriber.objects.get(unsubscribe_token=token)
    except Subscriber.DoesNotExist:
        return render(request, 'a_subscribers/token_expired.html', status=404)

    if subscriber.status != Subscriber.STATUS_UNSUBSCRIBED:
        subscriber.unsubscribe()

    return render(request, 'a_subscribers/unsubscribed.html')


def already_subscribed(request):
    return render(request, 'a_subscribers/already_subscribed.html')
