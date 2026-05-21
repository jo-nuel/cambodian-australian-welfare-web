from urllib.parse import quote_plus

from django.db import models
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index


def _org_settings():
    """Return the OrganisationSettings singleton, or None if not configured yet."""
    try:
        from a_home.models import OrganisationSettings
        return OrganisationSettings.load()
    except Exception:
        return None


class ContactSubmission(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    enquiry_area = models.CharField(max_length=80)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"

    def __str__(self):
        return f"{self.full_name} - {self.enquiry_area} ({self.submitted_at:%Y-%m-%d})"


class ContactPage(Page):
    template = "a_contact/contact_page.html"

    hero_title = models.CharField(max_length=180, blank=True)
    intro = RichTextField(blank=True)
    form_intro = RichTextField(blank=True)

    phone_number = models.CharField(max_length=30, blank=True)
    phone_support_text = models.CharField(max_length=180, blank=True)
    email_address = models.EmailField(blank=True)
    email_support_text = models.CharField(max_length=180, blank=True)

    location_name = models.CharField(max_length=160, blank=True)
    location_address = models.CharField(max_length=255, blank=True)
    location_suburb = models.CharField(max_length=160, blank=True)
    location_support_text = models.CharField(max_length=180, blank=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    visit_intro = RichTextField(blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    community_note = models.TextField(blank=True)

    notification_email = models.EmailField(
        blank=True,
        help_text='Optional. When someone submits the enquiry form, a copy is emailed here. Leave blank to use the email from Organisation Settings.',
    )

    search_fields = Page.search_fields + [
        index.SearchField("hero_title"),
        index.SearchField("intro"),
        index.SearchField("form_intro"),
        index.SearchField("phone_support_text"),
        index.SearchField("email_address"),
        index.SearchField("email_support_text"),
        index.SearchField("location_name"),
        index.SearchField("location_address"),
        index.SearchField("location_suburb"),
        index.SearchField("location_support_text"),
        index.SearchField("opening_hours"),
        index.SearchField("visit_intro"),
        index.SearchField("help_text"),
        index.SearchField("community_note"),
    ]

    parent_page_types = ["a_home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                HelpPanel(
                    'Fields left blank will show <strong>default placeholder text</strong> on the live site. '
                    'Phone, email, address, and opening hours fall back to your <strong>Organisation Settings</strong> '
                    '(Settings → Organisation Settings in the left menu) so you only need to update them in one place.'
                ),
                FieldPanel("hero_title"),
                FieldPanel("intro"),
                FieldPanel("form_intro"),
            ],
            heading="Intro",
        ),
        MultiFieldPanel(
            [
                HelpPanel(
                    'Leave the email blank to use the value from <em>Organisation Settings</em>. '
                    'The support text fields are the small descriptions shown below each contact method.'
                ),
                FieldPanel("email_address"),
                FieldPanel("email_support_text"),
            ],
            heading="Direct Contact",
        ),
        MultiFieldPanel(
            [
                FieldPanel("location_name"),
                FieldPanel("location_address"),
                FieldPanel("location_suburb"),
                FieldPanel("location_support_text"),
                FieldPanel("opening_hours"),
                FieldPanel("visit_intro"),
                FieldPanel("help_text"),
                FieldPanel("community_note"),
            ],
            heading="Visit Details",
        ),
        MultiFieldPanel(
            [
                HelpPanel(
                    'Each time someone submits the contact form, a copy is emailed to the address below. '
                    'Submissions are also saved under <em>Snippets → Contact submissions</em>. '
                    'Leave blank to use the email from Organisation Settings.'
                ),
                FieldPanel("notification_email"),
            ],
            heading="Form Notifications",
        ),
    ]

    class Meta:
        verbose_name = "Contact Page"

    @property
    def hero_title_display(self):
        return self.hero_title or "Get in touch with CAWC NSW"

    @property
    def intro_display(self):
        return self.intro or (
            "<p>We aim to make support and enquiry pathways simple, visible and welcoming. "
            "Reach out for general questions, referrals, community guidance or partnership discussions.</p>"
        )

    @property
    def form_intro_display(self):
        return self.form_intro or (
            "<p>Complete the form and a CAWC NSW team member will respond as soon as possible.</p>"
        )

    @property
    def phone_number_display(self):
        if self.phone_number:
            return self.phone_number
        org = _org_settings()
        return (org.phone_number if org else None) or "+61 2 9727 4336"

    @property
    def phone_support_text_display(self):
        return self.phone_support_text or (
            "Call for general enquiries, referrals, program information and support guidance."
        )

    @property
    def email_address_display(self):
        if self.email_address:
            return self.email_address
        org = _org_settings()
        return (org.email_address if org else None) or "cawcnsw@cambodianwelfare.org.au"

    @property
    def email_support_text_display(self):
        return self.email_support_text or (
            "Send an enquiry anytime and the team can respond with the right next steps."
        )

    @property
    def location_name_display(self):
        if self.location_name:
            return self.location_name
        org = _org_settings()
        return (org.street_address if org else None) or "Bonnyrigg Heights Community Centre"

    @property
    def location_address_display(self):
        if self.location_address:
            return self.location_address
        org = _org_settings()
        return (org.street_address if org else None) or "Bonnyrigg Heights Community Centre"

    @property
    def location_suburb_display(self):
        if self.location_suburb:
            return self.location_suburb
        org = _org_settings()
        return (org.suburb if org else None) or "Bonnyrigg Heights NSW 2177"

    @property
    def location_support_text_display(self):
        return self.location_support_text or (
            "Visit the centre for community support, information and program enquiries."
        )

    @property
    def location_chip_display(self):
        suburb = self.location_suburb_display.split(" NSW")[0].strip()
        return suburb or self.location_name_display

    @property
    def opening_hours_display(self):
        if self.opening_hours:
            return self.opening_hours
        org = _org_settings()
        return (org.opening_hours if org else None) or "Mon to Fri, 9:00am to 5:00pm"

    @property
    def visit_intro_display(self):
        return self.visit_intro or (
            "<p>Find our location, plan your visit, or contact the team first if you would like "
            "guidance before coming in.</p>"
        )

    @property
    def help_text_display(self):
        if self.help_text:
            return self.help_text
        org = _org_settings()
        email = (org.email_address if org else None) or "cawcnsw@cambodianwelfare.org.au"
        return f"Email us at {email} and we can help you plan your visit."

    @property
    def community_note_display(self):
        return self.community_note or (
            "We can help with referrals, program questions, partnership enquiries, "
            "and general support navigation."
        )

    @property
    def full_address_display(self):
        return ", ".join(
            part
            for part in [self.location_address_display, self.location_suburb_display]
            if part
        )

    @property
    def directions_url(self):
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(self.full_address_display)}"

    @property
    def phone_link(self):
        allowed = {"+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        digits = "".join(char for char in self.phone_number_display if char in allowed)
        return f"tel:{digits}"

    @property
    def email_link(self):
        return f"mailto:{self.email_address_display}"

    def serve(self, request):
        import logging
        from django.conf import settings as django_settings
        from django.core.mail import EmailMessage
        from a_contact.forms import ContactForm

        logger = logging.getLogger(__name__)

        if request.method == "POST":
            form = ContactForm(request.POST)
            if form.is_valid():
                submission = ContactSubmission.objects.create(
                    full_name=form.cleaned_data["full_name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data.get("phone", ""),
                    enquiry_area=form.cleaned_data["enquiry_area"],
                    message=form.cleaned_data["message"],
                )

                # Email notification to CAWC staff
                notify_to = self.notification_email
                if not notify_to:
                    org = _org_settings()
                    notify_to = org.email_address if org else None
                if notify_to:
                    try:
                        body = (
                            f"New contact form submission:\n\n"
                            f"Name: {submission.full_name}\n"
                            f"Email: {submission.email}\n"
                            f"Phone: {submission.phone or '—'}\n"
                            f"Enquiry area: {submission.enquiry_area}\n\n"
                            f"Message:\n{submission.message}\n\n"
                            f"Submitted: {submission.submitted_at:%Y-%m-%d %H:%M}"
                        )
                        EmailMessage(
                            subject=f"New contact enquiry from {submission.full_name}",
                            body=body,
                            from_email=django_settings.DEFAULT_FROM_EMAIL,
                            to=[notify_to],
                            reply_to=[submission.email] if submission.email else None,
                        ).send(fail_silently=True)
                    except Exception:
                        logger.exception("Failed to send contact notification email")

                return render(
                    request,
                    self.template,
                    {
                        "page": self,
                        "form": None,
                        "submitted": True,
                    },
                )
        else:
            form = ContactForm()

        return render(
            request,
            self.template,
            {
                "page": self,
                "form": form,
                "submitted": False,
            },
        )
