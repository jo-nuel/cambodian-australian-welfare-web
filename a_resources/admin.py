from django.contrib import admin

from .models import ResourceDownloadLead


@admin.register(ResourceDownloadLead)
class ResourceDownloadLeadAdmin(admin.ModelAdmin):
    list_display = ('email', 'resource_type', 'resource_title', 'created_at')
    list_filter = ('resource_type', 'created_at')
    search_fields = ('email', 'resource_title', 'resource_url')
    readonly_fields = ('email', 'resource_type', 'resource_title', 'resource_url', 'created_at')
