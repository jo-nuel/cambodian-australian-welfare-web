import csv
from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse

from .models import Subscriber


def export_confirmed_csv(modeladmin, request, queryset):
    confirmed = queryset.filter(status=Subscriber.STATUS_CONFIRMED)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="subscribers_{datetime.now().strftime("%Y%m%d")}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Email', 'Language Preference', 'Source', 'Confirmed At', 'Subscribed At'])
    for sub in confirmed:
        writer.writerow([
            sub.email,
            sub.get_language_preference_display(),
            sub.source,
            sub.confirmed_at.strftime('%Y-%m-%d %H:%M') if sub.confirmed_at else '',
            sub.subscribed_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response

export_confirmed_csv.short_description = 'Export selected (confirmed only) to CSV'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'status', 'language_preference', 'source', 'subscribed_at', 'confirmed_at']
    list_filter = ['status', 'language_preference', 'source']
    search_fields = ['email']
    readonly_fields = [
        'confirm_token', 'token_expires_at', 'unsubscribe_token',
        'subscribed_at', 'confirmed_at', 'unsubscribed_at',
    ]
    ordering = ['-subscribed_at']
    actions = [export_confirmed_csv]

    fieldsets = [
        ('Subscriber', {'fields': ['email', 'status', 'language_preference', 'source']}),
        ('Timestamps', {'fields': ['subscribed_at', 'confirmed_at', 'unsubscribed_at']}),
        ('Tokens', {'fields': ['confirm_token', 'token_expires_at', 'unsubscribe_token'], 'classes': ['collapse']}),
    ]
