import csv
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import path, reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags

from wagtail import hooks
from wagtail.admin import messages as wagtail_messages
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail.admin.widgets import Button
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .email import send_confirmation_email
from .models import Newsletter, Subscriber, _default_token, _default_token_expiry

logger = logging.getLogger(__name__)


# ── Permission helper ─────────────────────────────────────────────────────────

def _require_admin(request):
    """Return HttpResponseForbidden if user is not authenticated staff."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden()
    return None


def _audience_queryset(newsletter):
    qs = Subscriber.objects.filter(status=Subscriber.STATUS_CONFIRMED)
    if newsletter.audience == Newsletter.AUDIENCE_ENGLISH:
        return qs.filter(language_preference__in=[Subscriber.LANGUAGE_ENGLISH, Subscriber.LANGUAGE_ANY])
    if newsletter.audience == Newsletter.AUDIENCE_KHMER:
        return qs.filter(language_preference__in=[Subscriber.LANGUAGE_KHMER, Subscriber.LANGUAGE_ANY])
    return qs


# ── Subscriber: CSV export ───────────────────────────────────────────────────

def export_subscribers_csv(request):
    if denied := _require_admin(request):
        return denied
    qs = Subscriber.objects.filter(status=Subscriber.STATUS_CONFIRMED).order_by('-confirmed_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="cawc_subscribers_{datetime.now().strftime("%Y%m%d")}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Email', 'Language', 'Source', 'Confirmed Date', 'Subscribed Date'])
    for sub in qs:
        writer.writerow([
            sub.email,
            sub.get_language_preference_display(),
            sub.source,
            sub.confirmed_at.strftime('%Y-%m-%d') if sub.confirmed_at else '',
            sub.subscribed_at.strftime('%Y-%m-%d'),
        ])
    return response


# ── Subscriber: dashboard ────────────────────────────────────────────────────

def subscriber_dashboard(request):
    if denied := _require_admin(request):
        return denied

    by_language = [
        {
            'label': label,
            'count': Subscriber.objects.filter(
                status=Subscriber.STATUS_CONFIRMED,
                language_preference=value,
            ).count(),
        }
        for value, label in Subscriber.LANGUAGE_CHOICES
    ]

    stale_cutoff = timezone.now() - timedelta(days=7)

    return render(request, 'a_subscribers/subscriber_dashboard.html', {
        'total_confirmed': Subscriber.objects.filter(status=Subscriber.STATUS_CONFIRMED).count(),
        'total_pending': Subscriber.objects.filter(status=Subscriber.STATUS_PENDING).count(),
        'total_unsubscribed': Subscriber.objects.filter(status=Subscriber.STATUS_UNSUBSCRIBED).count(),
        'by_language': by_language,
        'stale_pending_count': Subscriber.objects.filter(
            status=Subscriber.STATUS_PENDING,
            subscribed_at__lt=stale_cutoff,
        ).count(),
    })


# ── Subscriber: resend stale pending ─────────────────────────────────────────

def resend_pending_confirmations(request):
    if denied := _require_admin(request):
        return denied

    stale_cutoff = timezone.now() - timedelta(days=7)
    stale_qs = Subscriber.objects.filter(
        status=Subscriber.STATUS_PENDING,
        subscribed_at__lt=stale_cutoff,
    )

    if request.method == 'POST':
        sent = 0
        failed = 0
        for subscriber in stale_qs:
            subscriber.confirm_token = _default_token()
            subscriber.token_expires_at = _default_token_expiry()
            subscriber.save(update_fields=['confirm_token', 'token_expires_at'])
            try:
                send_confirmation_email(subscriber)
                sent += 1
            except Exception:
                logger.exception('Failed to resend confirmation email to %s', subscriber.email)
                failed += 1

        if failed and sent:
            wagtail_messages.warning(
                request,
                f'Resent confirmation to {sent} pending subscriber{"s" if sent != 1 else ""}, '
                f'but {failed} email{"s" if failed != 1 else ""} could not be delivered. Check the server logs.',
            )
        elif failed:
            wagtail_messages.error(
                request,
                f'All {failed} resend{"s" if failed != 1 else ""} failed. Check email settings and server logs.',
            )
        else:
            wagtail_messages.success(
                request,
                f'Resent confirmation to {sent} pending subscriber{"s" if sent != 1 else ""}.',
            )
        return redirect(reverse('subscriber_dashboard'))

    return render(request, 'a_subscribers/resend_pending.html', {
        'stale_count': stale_qs.count(),
    })


# ── Newsletter: preview + send ───────────────────────────────────────────────

def newsletter_preview(request, pk):
    if denied := _require_admin(request):
        return denied
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, 'a_subscribers/newsletter_email.html', {
        'newsletter': newsletter,
        'unsubscribe_url': '#preview',
        'preview_mode': True,
    })


def newsletter_send_confirm(request, pk):
    if denied := _require_admin(request):
        return denied
    newsletter = get_object_or_404(Newsletter, pk=pk)
    list_url = reverse('wagtailsnippets_a_subscribers_newsletter:list')

    if newsletter.is_sent:
        wagtail_messages.error(request, 'This newsletter has already been sent.')
        return redirect(list_url)

    subscribers = _audience_queryset(newsletter)
    subscriber_count = subscribers.count()

    if request.method == 'POST':
        if subscriber_count == 0:
            wagtail_messages.error(request, 'No confirmed subscribers match the selected audience. Newsletter not sent.')
            return redirect(list_url)

        base = getattr(settings, 'NEWSLETTER_CONFIRM_URL_BASE', 'http://localhost:8000').rstrip('/')
        sent = 0
        failed = 0

        for subscriber in subscribers:
            unsubscribe_url = f'{base}/newsletter/unsubscribe/{subscriber.unsubscribe_token}/'
            html_body = render_to_string('a_subscribers/newsletter_email.html', {
                'newsletter': newsletter,
                'unsubscribe_url': unsubscribe_url,
                'preview_mode': False,
            }, request=request)
            plain_body = (
                f'{strip_tags(newsletter.body)}\n\n'
                f'---\n'
                f'You are receiving this because you subscribed to CAWC NSW updates.\n'
                f'Unsubscribe: {unsubscribe_url}'
            )
            try:
                send_mail(
                    subject=newsletter.subject,
                    message=plain_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    html_message=html_body,
                    fail_silently=False,
                )
                sent += 1
            except Exception:
                logger.exception('Failed to send newsletter "%s" to %s', newsletter.subject, subscriber.email)
                failed += 1

        if sent == 0:
            wagtail_messages.error(
                request,
                f'Send failed — all {failed} email{"s" if failed != 1 else ""} could not be delivered. '
                'Newsletter not marked as sent. Check your email settings.',
            )
            return redirect(list_url)

        newsletter.status = Newsletter.STATUS_SENT
        newsletter.sent_at = timezone.now()
        newsletter.recipient_count = sent
        newsletter.save(update_fields=['status', 'sent_at', 'recipient_count'])

        if failed:
            wagtail_messages.warning(
                request,
                f'Newsletter sent to {sent} subscriber{"s" if sent != 1 else ""}, '
                f'but {failed} email{"s" if failed != 1 else ""} could not be delivered.',
            )
        else:
            wagtail_messages.success(
                request,
                f'Newsletter sent to {sent} subscriber{"s" if sent != 1 else ""}.',
            )
        return redirect(list_url)

    return render(request, 'a_subscribers/newsletter_send_confirm.html', {
        'newsletter': newsletter,
        'subscriber_count': subscriber_count,
        'audience_label': newsletter.get_audience_display(),
        'can_send': subscriber_count > 0,
    })


# ── URL registration ─────────────────────────────────────────────────────────

@hooks.register('register_admin_urls')
def register_subscriber_admin_urls():
    return [
        path('subscribers/export-csv/', export_subscribers_csv, name='subscribers_export_csv'),
        path('subscribers/dashboard/', subscriber_dashboard, name='subscriber_dashboard'),
        path('subscribers/resend-pending/', resend_pending_confirmations, name='resend_pending_confirmations'),
        path('newsletter/<int:pk>/preview/', newsletter_preview, name='newsletter_preview'),
        path('newsletter/<int:pk>/send-confirm/', newsletter_send_confirm, name='newsletter_send_confirm'),
    ]


# ── Listing buttons for Newsletter ───────────────────────────────────────────

@hooks.register('construct_snippet_listing_buttons')
def add_newsletter_listing_buttons(buttons, snippet, user):
    if not isinstance(snippet, Newsletter):
        return
    buttons.append(Button(
        label='Preview',
        url=reverse('newsletter_preview', args=[snippet.pk]),
        icon_name='view',
        priority=10,
    ))
    if not snippet.is_sent:
        buttons.append(Button(
            label='Send',
            url=reverse('newsletter_send_confirm', args=[snippet.pk]),
            icon_name='mail',
            priority=20,
        ))


# ── Snippet registrations ────────────────────────────────────────────────────

class SubscriberViewSet(SnippetViewSet):
    model = Subscriber
    icon = 'mail'
    menu_label = 'Subscribers'
    menu_name = 'subscribers'
    add_to_admin_menu = False
    list_display = ['email', 'status_label', 'language_label', 'source', 'subscribed_at', 'confirmed_at']
    list_filter = ['status', 'language_preference']
    search_fields = ['email']
    ordering = ['-subscribed_at']
    list_per_page = 50


class NewsletterViewSet(SnippetViewSet):
    model = Newsletter
    icon = 'mail'
    menu_label = 'Newsletters'
    menu_name = 'newsletters'
    add_to_admin_menu = False
    list_display = ['subject', 'status_label', 'recipient_count', 'sent_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['subject']
    ordering = ['-created_at']
    list_per_page = 30


register_snippet(SubscriberViewSet)
register_snippet(NewsletterViewSet)


# ── "Subscribers" submenu ─────────────────────────────────────────────────────
# Single top-level "Subscribers" menu containing Dashboard, Subscribers list,
# Newsletters list, Resend to Pending, and Export CSV.

subscribers_submenu = Menu(items=[
    MenuItem(
        'Subscriber Dashboard',
        reverse_lazy('subscriber_dashboard'),
        icon_name='chart-bar',
        order=10,
    ),
    MenuItem(
        'Subscribers',
        reverse_lazy('wagtailsnippets_a_subscribers_subscriber:list'),
        icon_name='mail',
        order=20,
    ),
    MenuItem(
        'Newsletters',
        reverse_lazy('wagtailsnippets_a_subscribers_newsletter:list'),
        icon_name='doc-full',
        order=30,
    ),
    MenuItem(
        'Resend to Pending',
        reverse_lazy('resend_pending_confirmations'),
        icon_name='mail',
        order=40,
    ),
    MenuItem(
        'Export Subscribers CSV',
        reverse_lazy('subscribers_export_csv'),
        icon_name='download',
        order=50,
    ),
])


@hooks.register('register_admin_menu_item')
def register_subscribers_submenu():
    return SubmenuMenuItem(
        'Subscribers',
        subscribers_submenu,
        icon_name='mail',
        order=300,
    )
