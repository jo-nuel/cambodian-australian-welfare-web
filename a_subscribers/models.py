import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField


def _default_token():
    return uuid.uuid4().hex


def _default_token_expiry():
    return timezone.now() + timedelta(hours=48)


class Subscriber(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_UNSUBSCRIBED = 'unsubscribed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending confirmation'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_UNSUBSCRIBED, 'Unsubscribed'),
    ]

    LANGUAGE_ANY = 'any'
    LANGUAGE_ENGLISH = 'en'
    LANGUAGE_KHMER = 'km'
    LANGUAGE_CHOICES = [
        (LANGUAGE_ANY, 'Any / No preference'),
        (LANGUAGE_ENGLISH, 'English'),
        (LANGUAGE_KHMER, 'Khmer (ខ្មែរ)'),
    ]

    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    language_preference = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default=LANGUAGE_ANY)
    source = models.CharField(max_length=100, blank=True, help_text='Where the subscriber signed up, e.g. "footer", "homepage".')

    confirm_token = models.CharField(max_length=64, default=_default_token, unique=True, editable=False)
    token_expires_at = models.DateTimeField(default=_default_token_expiry)
    unsubscribe_token = models.CharField(max_length=64, default=_default_token, unique=True, editable=False)

    subscribed_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'

    def __str__(self):
        return f'{self.email} ({self.get_status_display()})'

    def is_token_valid(self):
        return timezone.now() < self.token_expires_at

    def confirm(self):
        self.status = self.STATUS_CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])

    def unsubscribe(self):
        self.status = self.STATUS_UNSUBSCRIBED
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['status', 'unsubscribed_at'])

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)

    def status_label(self):
        return self.get_status_display()
    status_label.short_description = 'Status'

    def language_label(self):
        return self.get_language_preference_display()
    language_label.short_description = 'Language'

    panels = [
        HelpPanel(
            'Subscribers sign up via the website. '
            'You can change someone\'s <strong>Status</strong> or <strong>Language preference</strong> here. '
            'All other fields are set automatically and cannot be edited.'
        ),
        MultiFieldPanel([
            FieldPanel('email', read_only=True),
            FieldPanel('status'),
            FieldPanel('language_preference'),
            FieldPanel('source', read_only=True),
        ], heading='Subscriber details'),
        MultiFieldPanel([
            FieldPanel('subscribed_at', read_only=True),
            FieldPanel('confirmed_at', read_only=True),
            FieldPanel('unsubscribed_at', read_only=True),
        ], heading='Dates'),
    ]


class Newsletter(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
    ]

    AUDIENCE_ALL = 'all'
    AUDIENCE_ENGLISH = 'en'
    AUDIENCE_KHMER = 'km'
    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, 'All confirmed subscribers'),
        (AUDIENCE_ENGLISH, 'English (includes "Any" preference)'),
        (AUDIENCE_KHMER, 'Khmer / ខ្មែរ (includes "Any" preference)'),
    ]

    subject = models.CharField(max_length=300, help_text='Subject line as it appears in the inbox.')
    preheader = models.CharField(
        max_length=200, blank=True,
        help_text='Short preview text shown after the subject in most email apps. Optional.',
    )
    body = RichTextField(help_text='Main newsletter content. Use headings, links, and bullet points as needed.')
    audience = models.CharField(
        max_length=5, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL,
        help_text='Who receives this newsletter. Subscribers with "Any" preference always receive all newsletters.',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'

    def __str__(self):
        return self.subject

    @property
    def is_sent(self):
        return self.status == self.STATUS_SENT

    def status_label(self):
        return self.get_status_display()
    status_label.short_description = 'Status'

    panels = [
        HelpPanel(
            'Compose your newsletter below. Use <strong>Preview</strong> in the listing to see how it looks '
            'before sending. Once sent, this newsletter is locked — you can view it but the email is already out.'
        ),
        HelpPanel(
            content=(
                '<details style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:12px 16px;">'
                '<summary style="cursor:pointer;font-weight:600;color:#1E6F56;">Need a starting point? Click to view newsletter templates</summary>'
                '<div style="margin-top:12px;font-size:13px;line-height:1.6;color:#374151;">'

                '<p style="margin:14px 0 4px;font-weight:700;color:#111;">Community Update</p>'
                '<p style="margin:0;color:#6b7280;">Brief intro · Recent program news · One upcoming event · Donate / Get involved CTA</p>'

                '<p style="margin:14px 0 4px;font-weight:700;color:#111;">Event Announcement</p>'
                '<p style="margin:0;color:#6b7280;">Event title · Date, time, location · What to expect · Register / Contact CTA</p>'

                '<p style="margin:14px 0 4px;font-weight:700;color:#111;">Program Highlight</p>'
                '<p style="margin:0;color:#6b7280;">Program summary · Who it supports · Story or photo · Get involved CTA</p>'

                '<p style="margin:14px 0 4px;font-weight:700;color:#111;">Resource Release</p>'
                '<p style="margin:0;color:#6b7280;">Resource title · What it covers · Why it matters · Download / Contact CTA</p>'

                '<p style="margin:14px 0 4px;font-weight:700;color:#111;">Volunteer Callout</p>'
                '<p style="margin:0;color:#6b7280;">Role summary · Time commitment · What you\'ll gain · Apply CTA</p>'

                '</div></details>'
            ),
        ),
        MultiFieldPanel([
            FieldPanel('subject'),
            FieldPanel('preheader'),
            FieldPanel('audience'),
        ], heading='Email header'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('status', read_only=True),
            FieldPanel('sent_at', read_only=True),
            FieldPanel('recipient_count', read_only=True),
        ], heading='Send record'),
    ]
