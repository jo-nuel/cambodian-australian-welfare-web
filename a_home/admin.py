from django.contrib import admin
from .models import GetInvolvedSubmission


@admin.register(GetInvolvedSubmission)
class GetInvolvedSubmissionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'interest', 'availability', 'submitted_at')
    list_filter = ('interest', 'availability')
    search_fields = ('full_name', 'email')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)
