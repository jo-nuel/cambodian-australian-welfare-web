from datetime import date

from django.db import models
from django.db.models import Q
from django.utils.html import strip_tags
from django.utils.text import Truncator
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index

EVENT_CATEGORY_CHOICES = [
    ('cultural',     'Cultural'),
    ('settlement',   'Settlement'),
    ('community',    'Community Support'),
    ('workshop',     'Workshop'),
    ('information',  'Information Session'),
    ('social',       'Social'),
]


# ── Individual event detail page ─────────────────────────────────────────────

class EventPage(Page):
    category = models.CharField(
        max_length=60,
        choices=EVENT_CATEGORY_CHOICES,
        blank=True,
        help_text='Category shown on event cards and the detail page.',
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Tick to pin this event as the featured spotlight on the Events page. Only one event should be featured at a time. If none are ticked, the next upcoming event is shown automatically.',
    )
    event_date = models.DateField(
        null=True, blank=True,
        help_text='Leave blank if the date is TBC.',
    )
    end_date = models.DateField(
        null=True, blank=True,
        help_text='Optional: end date for multi-day events.',
    )
    event_time = models.CharField(
        max_length=120, blank=True,
        help_text='e.g. "10am – 12pm" or "2:00pm – 4:30pm".',
    )
    venue = models.CharField(max_length=200, blank=True, help_text='Venue name, e.g. "Bonnyrigg Heights Community Centre".')
    address = models.CharField(
        max_length=300, blank=True,
        help_text='Full street address, e.g. "1 Smith St, Bonnyrigg NSW 2177". Shown below the venue name.',
    )
    cost = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. "Free", "By registration" or "$5 per person". Leave blank to hide this field.',
    )
    language = models.CharField(
        max_length=100, blank=True,
        help_text='e.g. "Khmer and English".',
    )
    summary = models.CharField(
        max_length=280, blank=True,
        help_text='Short summary shown on event cards (auto-generated from body if blank).',
    )
    body = RichTextField(
        blank=True,
        help_text='Full event description shown on the detail page.',
    )
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    registration_link = models.CharField(
        max_length=255, blank=True,
        help_text='External RSVP or registration URL.',
    )
    registration_text = models.CharField(
        max_length=80, blank=True,
        help_text='Registration button label, e.g. "Register Now" or "RSVP by 30 June".',
    )

    search_fields = Page.search_fields + [
        index.SearchField('category'),
        index.SearchField('summary'),
        index.SearchField('body'),
        index.SearchField('event_time'),
        index.SearchField('venue'),
        index.SearchField('address'),
        index.SearchField('cost'),
        index.SearchField('language'),
    ]

    parent_page_types = ['a_events.EventsPage']
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('category'),
            FieldPanel('is_featured'),
            FieldPanel('featured_image'),
            FieldPanel('summary'),
        ], heading='Card / Overview'),
        MultiFieldPanel([
            FieldPanel('event_date'),
            FieldPanel('end_date'),
            FieldPanel('event_time'),
            FieldPanel('venue'),
            FieldPanel('address'),
            FieldPanel('cost'),
            FieldPanel('language'),
        ], heading='Event Details'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('registration_link'),
            FieldPanel('registration_text'),
        ], heading='Registration'),
    ]

    class Meta:
        verbose_name = 'Event Page'

    # ── Display helpers ──────────────────────────────────────────────────────

    @property
    def category_display(self):
        return dict(EVENT_CATEGORY_CHOICES).get(self.category, self.category or 'Event')

    @property
    def is_upcoming(self):
        if self.event_date:
            return self.event_date >= date.today()
        return True  # no date = TBC, treat as upcoming

    @property
    def summary_display(self):
        if self.summary:
            return self.summary
        if self.body:
            return Truncator(strip_tags(self.body)).chars(220)
        return ''

    @property
    def has_logistics(self):
        return bool(self.event_time or self.venue)

    @property
    def has_registration(self):
        return bool(self.registration_link)

    @property
    def registration_cta(self):
        return {
            'text': self.registration_text or 'Register Now',
            'link': self.registration_link,
        }


# ── Events index / landing page ──────────────────────────────────────────────

class FeaturedDetailBlock(blocks.CharBlock):
    pass


class EventsPage(Page):
    intro = models.TextField(
        blank=True,
        default=(
            'Our events are posted on Facebook. Follow us to stay up to date '
            'with the latest programs, workshops, and community gatherings.'
        ),
        help_text='Description paragraph shown under the page title.',
    )
    facebook_button_text = models.CharField(
        max_length=80,
        blank=True,
        default='View our events on Facebook',
        help_text='Label on the Facebook button.',
    )
    facebook_url = models.URLField(
        blank=True,
        default='https://www.facebook.com/cambodianwelfare',
        help_text='Facebook page URL for the button.',
    )

    # Legacy fields kept so existing data/migrations are not broken
    featured_label = models.CharField(max_length=80, blank=True)
    featured_title = models.CharField(max_length=120, blank=True)
    featured_summary = models.TextField(blank=True)
    featured_date_text = models.CharField(max_length=120, blank=True)
    featured_time_text = models.CharField(max_length=120, blank=True)
    featured_venue_text = models.CharField(max_length=120, blank=True)
    featured_entry_text = models.CharField(max_length=120, blank=True)
    featured_details = StreamField([
        ('detail', FeaturedDetailBlock()),
    ], blank=True, use_json_field=True)
    featured_cta_text = models.CharField(max_length=80, blank=True)
    featured_cta_link = models.CharField(max_length=255, blank=True)
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    featured_map_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    parent_page_types = ['a_home.HomePage']
    subpage_types = ['a_events.EventPage']

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('facebook_button_text'),
        FieldPanel('facebook_url'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        today = date.today()

        child_events = (
            EventPage.objects
            .child_of(self)
            .live()
            .public()
        )
        has_child = child_events.exists()

        if has_child:
            # Upcoming: date is TBC (null) or date >= today
            upcoming_qs = child_events.filter(
                Q(event_date__isnull=True) | Q(event_date__gte=today)
            ).order_by('event_date')

            # Past: date < today
            past_qs = child_events.filter(
                event_date__lt=today
            ).order_by('-event_date')

            # Featured: manually pinned, else first upcoming
            featured = child_events.filter(is_featured=True).first()
            if not featured:
                featured = upcoming_qs.first()

            if featured:
                upcoming_qs = upcoming_qs.exclude(pk=featured.pk)

            context['featured_event'] = featured
            context['upcoming_events'] = list(upcoming_qs[:9])
            context['past_events'] = list(past_qs[:3])

        context['has_child_events'] = has_child
        return context

    @property
    def intro_display(self):
        return self.intro or (
            'Our events are posted on Facebook. Follow us to stay up to date '
            'with the latest programs, workshops, and community gatherings.'
        )

    @property
    def facebook_button_text_display(self):
        return self.facebook_button_text or 'View our events on Facebook'

    @property
    def facebook_url_display(self):
        return self.facebook_url or 'https://www.facebook.com/cambodianwelfare'
