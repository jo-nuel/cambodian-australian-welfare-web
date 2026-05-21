from django.contrib import admin

from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "enquiry_area", "submitted_at")
    list_filter = ("enquiry_area", "submitted_at")
    search_fields = ("full_name", "email", "message")
    ordering = ("-submitted_at",)
