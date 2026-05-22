from datetime import date
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.shortcuts import render
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from wagtail.search import index


# ── Block definitions ─────────────────────────────────────────────────────────

class LinkBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    link = blocks.URLBlock()


class StatCardBlock(blocks.StructBlock):
    value = blocks.CharBlock(
        max_length=20,
        help_text='Short metric, e.g. "100+", "1,200", "20 years".',
    )
    label = blocks.CharBlock(
        help_text='Metric label, e.g. "Active Volunteers".',
    )
    description = blocks.CharBlock(
        required=False,
        help_text='Optional one-line supporting detail.',
    )


class PartnerLogoBlock(blocks.StructBlock):
    name = blocks.CharBlock(help_text='Partner or funder organisation name.')
    logo = ImageChooserBlock()
    url = blocks.URLBlock(required=False, help_text='Optional website link for this partner.')

    class Meta:
        icon = 'image'


class SupportCardBlock(blocks.StructBlock):
    """Legacy block — kept so existing page data is not lost."""
    icon_label = blocks.CharBlock(required=False, max_length=12)
    title = blocks.CharBlock()
    description = blocks.TextBlock()


class ProgramCardBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    summary = blocks.TextBlock()
    image = ImageChooserBlock(required=False)
    category = blocks.CharBlock(
        required=False,
        help_text='e.g. "Seniors Hub", "Women\'s Support".',
    )
    link = blocks.CharBlock(
        required=False,
        help_text='Relative or absolute URL for this program page.',
    )


class EventCardBlock(blocks.StructBlock):
    date = blocks.DateBlock()
    title = blocks.CharBlock()
    location = blocks.CharBlock(required=False)
    description = blocks.TextBlock(required=False)
    cta_text = blocks.CharBlock(required=False, default='Details')
    cta_link = blocks.URLBlock(required=False)


class DonationStepBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    description = blocks.TextBlock()


class DonationImpactCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(help_text='e.g. "Programs", "Outreach", "Cultural Connection".')
    description = blocks.TextBlock()
    amount_example = blocks.CharBlock(
        required=False,
        help_text='Optional anchor amount, e.g. "$50 funds program materials for one session."',
    )


class FAQBlock(blocks.StructBlock):
    question = blocks.CharBlock()
    answer = blocks.RichTextBlock(required=False)


# ── Page model ────────────────────────────────────────────────────────────────

class HomePage(Page):

    # ── Hero ─────────────────────────────────────────────────────────────────
    hero_eyebrow = models.CharField(max_length=120, blank=True)
    hero_title = models.CharField(max_length=200, blank=True)
    hero_description = models.TextField(blank=True)
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Fallback image used in the hero if no photos are added to the Hero Photo Display below. Upload here for a single static image.',
    )
    primary_cta_text = models.CharField(max_length=80, blank=True, help_text='e.g. "Donate Now"')
    primary_cta_link = models.CharField(max_length=500, blank=True, help_text='Link for the primary button. Use "#donate" to open the donation modal.')
    secondary_cta_text = models.CharField(max_length=80, blank=True, help_text='e.g. "View Programs"')
    secondary_cta_link = models.CharField(max_length=500, blank=True, help_text='Link for the secondary button, e.g. "/programs/"')

    # ── Introduction ──────────────────────────────────────────────────────────
    intro_title = models.CharField(max_length=200, blank=True)
    intro_text = RichTextField(blank=True)

    # ── Impact stats ──────────────────────────────────────────────────────────
    impact_stats = StreamField([
        ('stat', StatCardBlock()),
    ], blank=True, use_json_field=True)

    # ── Featured programs ─────────────────────────────────────────────────────
    featured_programs = StreamField([
        ('program', ProgramCardBlock()),
    ], blank=True, use_json_field=True)

    # ── Events ────────────────────────────────────────────────────────────────
    upcoming_events_intro = models.TextField(blank=True)
    upcoming_events = StreamField([
        ('event', EventCardBlock()),
    ], blank=True, use_json_field=True)

    # ── Donation ──────────────────────────────────────────────────────────────
    donation_section_title = models.CharField(max_length=200, blank=True)
    donation_description = models.TextField(blank=True)
    donation_cta_text = models.CharField(max_length=80, blank=True)
    donation_cta_link = models.CharField(max_length=500, blank=True)
    donation_steps = StreamField([
        ('step', DonationStepBlock()),
    ], blank=True, use_json_field=True)

    # ── Volunteer ─────────────────────────────────────────────────────────────
    volunteer_title = models.CharField(max_length=120, blank=True)
    volunteer_description = models.TextField(blank=True)
    volunteer_cta_text = models.CharField(max_length=80, blank=True)
    volunteer_cta_link = models.CharField(max_length=500, blank=True)
    volunteer_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    # ── FAQ ───────────────────────────────────────────────────────────────────
    faq_items = StreamField([
        ('faq', FAQBlock()),
    ], blank=True, use_json_field=True)

    # ── Community photo strip ─────────────────────────────────────────────────
    photo_strip = StreamField([
        ('image', ImageChooserBlock()),
    ], blank=True, use_json_field=True)

    # ── Partners & Supporters ─────────────────────────────────────────────────
    show_partners = models.BooleanField(
        default=False,
        help_text='Tick to show the Partners & Supporters section on the homepage.',
    )
    partners_logos = StreamField([
        ('partner', PartnerLogoBlock()),
    ], blank=True, use_json_field=True)

    # ── Legacy / fallback ─────────────────────────────────────────────────────
    support_cards = StreamField([
        ('card', SupportCardBlock()),
    ], blank=True, use_json_field=True)

    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='title')),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('button', LinkBlock()),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('hero_eyebrow'),
        index.SearchField('hero_title'),
        index.SearchField('hero_description'),
        index.SearchField('intro_title'),
        index.SearchField('intro_text'),
        index.SearchField('impact_stats'),
        index.SearchField('donation_section_title'),
        index.SearchField('donation_description'),
        index.SearchField('volunteer_title'),
        index.SearchField('volunteer_description'),
        index.SearchField('faq_items'),
        index.SearchField('body'),
    ]

    # ── Wagtail admin panels ──────────────────────────────────────────────────

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                'Most fields below show <strong>default placeholder text</strong> on the live site if left '
                'blank. Fill them in to replace the defaults with your own content. Hover over any field for '
                'specific guidance.'
            ),
            FieldPanel('hero_eyebrow'),
            FieldPanel('hero_title'),
            FieldPanel('hero_description'),
            FieldPanel('hero_image'),
            FieldPanel('primary_cta_text'),
            FieldPanel('primary_cta_link'),
            FieldPanel('secondary_cta_text'),
            FieldPanel('secondary_cta_link'),
        ], heading='Hero'),
        MultiFieldPanel([
            FieldPanel('intro_title'),
            FieldPanel('intro_text'),
        ], heading='Introduction'),
        MultiFieldPanel([
            FieldPanel('impact_stats'),
        ], heading='Impact Stats'),
        MultiFieldPanel([
            FieldPanel('donation_section_title'),
            FieldPanel('donation_description'),
            FieldPanel('donation_cta_text'),
            FieldPanel('donation_cta_link'),
            FieldPanel('donation_steps'),
        ], heading='Donation Section'),
        MultiFieldPanel([
            FieldPanel('volunteer_title'),
            FieldPanel('volunteer_description'),
            FieldPanel('volunteer_cta_text'),
            FieldPanel('volunteer_cta_link'),
            FieldPanel('volunteer_image'),
        ], heading='Volunteer Call To Action'),
        MultiFieldPanel([
            HelpPanel(
                'These FAQs appear on the <em>homepage only</em>. They are <strong>separate from the main '
                'FAQ page</strong> — if you want the same question on both, you need to add it in both places.'
            ),
            FieldPanel('faq_items'),
        ], heading='FAQs (homepage only)'),
        MultiFieldPanel([
            HelpPanel('These photos rotate automatically in the large image on the right side of the homepage hero. Add at least one photo. Landscape images work best — minimum 1 800 px wide, JPEG or PNG format.'),
            FieldPanel('photo_strip'),
        ], heading='Hero Photo Display'),
        MultiFieldPanel([
            HelpPanel(
                'This section is <strong>hidden by default</strong>. Tick "Show partners section" '
                'and add logos below to make it visible on the homepage. Only enable this once '
                'CAWC has written permission to display each organisation\'s logo.'
            ),
            FieldPanel('show_partners'),
            FieldPanel('partners_logos'),
        ], heading='Partners & Supporters'),
    ]

    # ── Utility ───────────────────────────────────────────────────────────────

    def _first_body_value(self, block_type):
        for block in self.body:
            if block.block_type == block_type:
                return block.value
        return None

    # ── Hero display properties ───────────────────────────────────────────────

    @property
    def hero_display_eyebrow(self):
        return self.hero_eyebrow or 'Community-led support since 1983'

    @property
    def hero_display_title(self):
        return self.hero_title or 'Supporting Cambodian families and communities across NSW'

    @property
    def hero_display_description(self):
        return self.hero_description or self._first_body_value('paragraph') or (
            'CAWC NSW is a community-led not-for-profit supporting Cambodian Australians '
            'through culturally responsive programs, advocacy, settlement support, events '
            'and practical pathways to connection.'
        )

    @property
    def hero_display_image(self):
        return self.hero_image or self._first_body_value('image')

    @property
    def primary_cta(self):
        if self.primary_cta_text and self.primary_cta_link:
            return {'text': self.primary_cta_text, 'link': self.primary_cta_link}
        fallback = self._first_body_value('button')
        if fallback:
            return fallback
        return {'text': 'Donate Now', 'link': '/#donate'}

    @property
    def secondary_cta(self):
        if self.secondary_cta_text and self.secondary_cta_link:
            return {'text': self.secondary_cta_text, 'link': self.secondary_cta_link}
        return {'text': 'View Programs', 'link': '/programs/'}

    # ── Introduction display properties ───────────────────────────────────────

    @property
    def intro_title_display(self):
        return self.intro_title or 'A trusted community connection point'

    # ── Impact stats display properties ───────────────────────────────────────

    @property
    def impact_stats_display(self):
        # First preference: live records flagged `display_on_homepage` from the
        # current Impact Reporting Period. Falls back through the StreamField
        # and then the hardcoded baseline so the homepage never renders empty.
        try:
            from a_impact.models import ImpactMetric, ImpactReportPeriod
            current_period = (
                ImpactReportPeriod.objects.filter(is_current=True).first()
                or ImpactReportPeriod.objects.order_by('-end_date', '-created_at').first()
            )
            if current_period:
                metrics = ImpactMetric.objects.filter(
                    reporting_period=current_period,
                    display_on_homepage=True,
                ).order_by('sort_order', 'title')[:6]
                if metrics:
                    return [
                        {
                            'value': f'{m.value} {m.get_unit_display()}'.strip() if m.unit else m.value,
                            'label': m.title,
                            'description': m.description,
                        }
                        for m in metrics
                    ]
        except Exception:
            pass

        if self.impact_stats:
            return [block.value for block in self.impact_stats]
        return [
            {
                'value': '1983',
                'label': 'Established',
                'description': 'Founded as Khmer Interagency by workers supporting Khmer communities.',
            },
            {
                'value': '1996',
                'label': 'Incorporated',
                'description': 'Formalised as the Cambodian-Australian Welfare Council of NSW Inc.',
            },
            {
                'value': '7',
                'label': 'Core Objectives',
                'description': 'Guiding culture, service access, community harmony and advocacy.',
            },
        ]

    # ── Featured programs display properties ──────────────────────────────────

    @property
    def featured_programs_display(self):
        # Auto-pull from real ProgramPage children — keeps homepage in sync with
        # the Programs section automatically. Manual StreamField acts as an
        # explicit override only when filled in.
        if self.featured_programs:
            return [block.value for block in self.featured_programs]
        try:
            from a_programs.models import ProgramPage
        except ImportError:
            ProgramPage = None

        if ProgramPage:
            programs = (
                ProgramPage.objects.live().public()
                .order_by('path')[:3]
            )
            program_list = [p.specific for p in programs]
            if program_list:
                return [
                    {
                        'title': program.title,
                        'summary': program.summary_display,
                        'image': program.featured_image,
                        'category': program.category_display,
                        'link': program.url,
                    }
                    for program in program_list
                ]
        return [
            {
                'title': 'Cambodian Seniors Hub',
                'summary': (
                    'A regular safe space for Cambodian seniors to connect, share morning tea, '
                    'take part in gentle activities and learn about local services.'
                ),
                'image': None,
                'category': 'Seniors',
                'link': '/programs/cambodian-seniors-hub/',
            },
            {
                'title': 'Settlement Engagement and Transition Support',
                'summary': (
                    'Support for eligible humanitarian entrants and newly arrived Cambodian '
                    'migrants as they build independence, confidence and community connection.'
                ),
                'image': None,
                'category': 'Settlement',
                'link': '/programs/settlement-engagement-and-transition-support-program-sets/',
            },
            {
                'title': 'Cambodian Children Support Project',
                'summary': (
                    'Homework help, tutoring and school holiday activities that support confidence, '
                    'literacy, numeracy and school transition for Cambodian children.'
                ),
                'image': None,
                'category': 'Children and families',
                'link': '/programs/cambodian-children-support-project/',
            },
        ]

    def _program_homepage_category(self, program):
        categories = {
            'cambodian-seniors-hub': 'Seniors',
            'sets': 'Settlement',
            'children-support-project': 'Children and Families',
            'cyber-security': 'Digital Safety',
            'khmer-elderly-day-care': 'Elder Care',
            'laotian-social-support': 'Social Support',
            'women-support-hub': 'Women and Families',
        }
        return categories.get(program.program_tag) or program.title

    # ── Events display properties ─────────────────────────────────────────────

    @property
    def upcoming_events_intro_display(self):
        return self.upcoming_events_intro or (
            'Upcoming events help community members connect, learn and take part '
            'in CAWC NSW programs.'
        )

    @property
    def upcoming_events_display(self):
        # Auto-pull from real EventPage children — same data as the Events page,
        # automatically kept in sync. Manual StreamField acts as an explicit override.
        if self.upcoming_events:
            return [block.value for block in self.upcoming_events]
        try:
            from a_events.models import EventPage
            from django.db.models import Q
            today = date.today()
            events = list(
                EventPage.objects.live().public()
                .filter(Q(event_date__isnull=True) | Q(event_date__gte=today))
                .order_by('event_date')[:3]
            )
            if events:
                return [
                    {
                        'date': event.event_date,
                        'title': event.title,
                        'location': event.venue,
                        'description': event.summary_display,
                        'cta_text': 'View details',
                        'cta_link': event.url,
                    }
                    for event in events
                ]
        except Exception:
            pass
        return [
            {
                'date': date(2026, 6, 4),
                'title': 'Community Information Session',
                'location': 'Fairfield, NSW',
                'description': (
                    'A welcoming session for sharing local service information, '
                    'referrals and practical community support.'
                ),
                'cta_text': 'View details',
                'cta_link': '/events/',
            },
            {
                'date': date(2026, 6, 18),
                'title': 'Volunteer Welcome Day',
                'location': 'Bonnyrigg Heights Community Centre',
                'description': (
                    'Meet the team, learn how CAWC programs operate, and explore '
                    'practical ways to contribute to community activities.'
                ),
                'cta_text': 'View details',
                'cta_link': '/events/',
            },
            {
                'date': date(2026, 7, 9),
                'title': 'Women and Family Support Workshop',
                'location': 'Cabramatta, NSW',
                'description': (
                    'A community education workshop focused on family wellbeing, '
                    'safety information and referral pathways.'
                ),
                'cta_text': 'View details',
                'cta_link': '/events/',
            },
        ]

    # ── Donation display properties ───────────────────────────────────────────

    @property
    def donation_section_title_display(self):
        return self.donation_section_title or 'Help keep community support accessible'

    @property
    def donation_description_display(self):
        return self.donation_description or (
            'Your support helps CAWC continue culturally responsive programs, outreach, '
            'workshops and community activities for Cambodian families, seniors, women, '
            'children and newly arrived community members.'
        )

    @property
    def donation_cta_display(self):
        if self.donation_cta_text and self.donation_cta_link:
            return {'text': self.donation_cta_text, 'link': self.donation_cta_link}
        return {'text': 'Donate Now', 'link': '/#donate'}

    @property
    def donation_steps_display(self):
        if self.donation_steps:
            return [block.value for block in self.donation_steps]
        return [
            {
                'title': 'Support community services',
                'description': (
                    'Contribute to practical assistance, referrals and culturally safe '
                    'guidance for families, seniors and newly arrived community members.'
                ),
            },
            {
                'title': 'Sustain programs',
                'description': (
                    'Help keep wellbeing activities, educational workshops and social '
                    'connection programs accessible.'
                ),
            },
            {
                'title': 'Strengthen connection',
                'description': (
                    'Support community events, intergenerational activities and outreach '
                    'that reduce isolation.'
                ),
            },
            {
                'title': 'Build long-term capacity',
                'description': (
                    'Strengthen the organisation so CAWC can keep responding to '
                    'community needs over time.'
                ),
            },
        ]

    # ── Volunteer display properties ──────────────────────────────────────────

    @property
    def volunteer_cta_display(self):
        return {
            'title': self.volunteer_title or 'Volunteer with CAWC NSW',
            'description': self.volunteer_description or (
                'Support community events, outreach, program activities and culturally '
                'responsive services by registering your interest with the CAWC team.'
            ),
            'text': self.volunteer_cta_text or 'Express Interest',
            'link': self.volunteer_cta_link or '/get-involved/',
        }

    @property
    def volunteer_image_display(self):
        """Prefer dedicated volunteer image; fall back to hero image."""
        return self.volunteer_image or self.hero_image or self._first_body_value('image')

    # ── FAQ display properties ────────────────────────────────────────────────

    @property
    def faq_items_display(self):
        # Prefer locally-added FAQs (existing pattern), then fall back to
        # shared FAQ snippets marked "show_on_homepage", then hardcoded defaults.
        if self.faq_items:
            return [block.value for block in self.faq_items]
        try:
            from a_about.models import FAQ
            homepage_faqs = FAQ.objects.filter(show_on_homepage=True).order_by('sort_order', 'question')[:4]
            if homepage_faqs.exists():
                return [
                    {'question': f.question, 'answer': f.answer}
                    for f in homepage_faqs
                ]
        except Exception:
            pass
        return [
            {
                'question': 'Who does CAWC support?',
                'answer': (
                    '<p>CAWC supports Cambodian families and community members in NSW, '
                    'including seniors, women, children, newly arrived migrants and people '
                    'seeking culturally responsive information or referrals.</p>'
                ),
            },
            {
                'question': 'How can I become a volunteer?',
                'answer': (
                    '<p>You can register your interest through the Get Involved page or speak '
                    'with the team during community events and program sessions.</p>'
                ),
            },
            {
                'question': 'How do donations help?',
                'answer': (
                    '<p>Donations help sustain community programs, workshops, outreach, events '
                    'and practical support. Specific donation details should be confirmed by '
                    'CAWC before launch.</p>'
                ),
            },
            {
                'question': 'Where can I find upcoming activities?',
                'answer': (
                    '<p>Visit the Events page for upcoming sessions and community activities. '
                    'Event details can be updated by CAWC staff in Wagtail.</p>'
                ),
            },
        ]

    # ── Photo strip display properties ────────────────────────────────────────

    @property
    def photo_strip_display(self):
        if self.photo_strip:
            return [block.value for block in self.photo_strip]
        return []

    @property
    def hero_running_display(self):
        if self.photo_strip:
            return [
                {
                    'kind': 'wagtail',
                    'image': block.value,
                }
                for block in self.photo_strip
            ]

        folder = Path(settings.MEDIA_ROOT) / 'Photos of running display'
        if folder.exists():
            supported = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}
            images = []
            for file_path in sorted(folder.iterdir()):
                if file_path.is_file() and file_path.suffix.lower() in supported:
                    relative_path = file_path.relative_to(settings.MEDIA_ROOT).as_posix()
                    images.append({
                        'kind': 'media',
                        'url': f"{settings.MEDIA_URL}{quote(relative_path)}",
                        'alt': file_path.stem.replace('_', ' ').replace('-', ' '),
                    })
            if images:
                return images

        if self.hero_display_image:
            return [{
                'kind': 'wagtail',
                'image': self.hero_display_image,
            }]
        return []

    class Meta:
        verbose_name = 'Home Page'


# ── Get Involved submission ───────────────────────────────────────────────────

class GetInvolvedSubmission(models.Model):
    full_name    = models.CharField(max_length=120)
    email        = models.EmailField()
    phone        = models.CharField(max_length=30, blank=True)
    interest     = models.CharField(max_length=40)
    availability = models.CharField(max_length=40)
    skills       = models.TextField(blank=True)
    message      = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Get Involved Submission'
        verbose_name_plural = 'Get Involved Submissions'

    def __str__(self):
        return f'{self.full_name} — {self.interest} ({self.submitted_at:%Y-%m-%d})'


# ── Get Involved page ─────────────────────────────────────────────────────────

class RoleCardBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    description = blocks.TextBlock()
    commitment = blocks.CharBlock(required=False, help_text='e.g. "Flexible hours" or "2 days/week"')
    icon = blocks.CharBlock(required=False, help_text='Optional short label or emoji.')

    class Meta:
        icon = 'user'


class GetInvolvedPage(Page):
    intro = RichTextField(blank=True)
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    # ── Volunteer section ─────────────────────────────────────────────────────
    volunteer_heading = models.CharField(max_length=120, blank=True)
    volunteer_intro = RichTextField(blank=True)
    volunteer_roles = StreamField([
        ('role', RoleCardBlock(label='Role')),
    ], blank=True, use_json_field=True)

    # ── Internship section ────────────────────────────────────────────────────
    internship_heading = models.CharField(max_length=120, blank=True)
    internship_intro = RichTextField(blank=True)
    internship_roles = StreamField([
        ('role', RoleCardBlock(label='Role')),
    ], blank=True, use_json_field=True)

    # ── Expression of Interest section ────────────────────────────────────────
    eoi_heading = models.CharField(max_length=120, blank=True)
    eoi_intro = RichTextField(blank=True)
    notification_email = models.EmailField(
        blank=True,
        help_text='Optional. When someone submits the Expression of Interest form, a copy is emailed here. Leave blank to use the email from Organisation Settings.',
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('volunteer_heading'),
        index.SearchField('volunteer_intro'),
        index.SearchField('volunteer_roles'),
        index.SearchField('internship_heading'),
        index.SearchField('internship_intro'),
        index.SearchField('internship_roles'),
        index.SearchField('eoi_heading'),
        index.SearchField('eoi_intro'),
    ]

    parent_page_types = ['a_home.HomePage']
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('featured_image'),
        MultiFieldPanel([
            FieldPanel('volunteer_heading'),
            FieldPanel('volunteer_intro'),
            FieldPanel('volunteer_roles'),
        ], heading='Volunteer Section'),
        MultiFieldPanel([
            FieldPanel('internship_heading'),
            FieldPanel('internship_intro'),
            FieldPanel('internship_roles'),
        ], heading='Internship Section'),
        MultiFieldPanel([
            HelpPanel(
                'Each time someone submits the Expression of Interest form, a copy is emailed to '
                'the address below. Submissions are also saved in the database under '
                '<em>Snippets → Get Involved submissions</em>.'
            ),
            FieldPanel('eoi_heading'),
            FieldPanel('eoi_intro'),
            FieldPanel('notification_email'),
        ], heading='Expression of Interest'),
    ]

    class Meta:
        verbose_name = 'Get Involved Page'

    # ── Display properties ────────────────────────────────────────────────────

    @property
    def intro_display(self):
        return self.intro or (
            '<p>There are many ways to contribute to CAWC NSW — whether you volunteer your '
            'time, join as an intern, or express your interest in a specific role. '
            'Every contribution helps strengthen our community.</p>'
        )

    @property
    def volunteer_heading_display(self):
        return self.volunteer_heading or 'Volunteer'

    @property
    def volunteer_intro_display(self):
        return self.volunteer_intro or (
            '<p>Volunteers are the backbone of CAWC NSW. Whether you can offer a few hours '
            'a week or contribute specialist skills, your time makes a real difference '
            'to Cambodian families across New South Wales.</p>'
        )

    @property
    def volunteer_roles_display(self):
        return [block.value for block in self.volunteer_roles] if self.volunteer_roles else []

    @property
    def internship_heading_display(self):
        return self.internship_heading or 'Internship'

    @property
    def internship_intro_display(self):
        return self.internship_intro or (
            '<p>CAWC NSW offers internship placements for students and recent graduates '
            'looking to gain hands-on experience in community services, social work, '
            'administration and communications.</p>'
        )

    @property
    def internship_roles_display(self):
        return [block.value for block in self.internship_roles] if self.internship_roles else []

    @property
    def eoi_heading_display(self):
        return self.eoi_heading or 'Express Your Interest'

    @property
    def eoi_intro_display(self):
        return self.eoi_intro or (
            '<p>Ready to get involved? Fill in the form below and our team will be in '
            'touch to discuss how you can contribute.</p>'
        )

    # ── Form handling ─────────────────────────────────────────────────────────

    def serve(self, request):
        import logging
        from django.conf import settings as django_settings
        from django.core.mail import EmailMessage
        from a_home.forms import GetInvolvedForm

        logger = logging.getLogger(__name__)

        if request.method == 'POST':
            form = GetInvolvedForm(request.POST)
            if form.is_valid():
                submission = GetInvolvedSubmission.objects.create(
                    full_name=form.cleaned_data['full_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data.get('phone', ''),
                    interest=form.cleaned_data['interest'],
                    availability=form.cleaned_data['availability'],
                    skills=form.cleaned_data.get('skills', ''),
                    message=form.cleaned_data.get('message', ''),
                )

                # Email notification to CAWC staff
                notify_to = self.notification_email
                if not notify_to:
                    org = OrganisationSettings.load()
                    notify_to = org.email_address if org else None
                if notify_to:
                    try:
                        body = (
                            f'New Expression of Interest submission:\n\n'
                            f'Name: {submission.full_name}\n'
                            f'Email: {submission.email}\n'
                            f'Phone: {submission.phone or "—"}\n'
                            f'Interest: {submission.interest}\n'
                            f'Availability: {submission.availability}\n'
                            f'Skills: {submission.skills or "—"}\n\n'
                            f'Message:\n{submission.message or "—"}\n\n'
                            f'Submitted: {submission.submitted_at:%Y-%m-%d %H:%M}'
                        )
                        EmailMessage(
                            subject=f'New Get Involved enquiry from {submission.full_name}',
                            body=body,
                            from_email=django_settings.DEFAULT_FROM_EMAIL,
                            to=[notify_to],
                            reply_to=[submission.email] if submission.email else None,
                        ).send(fail_silently=True)
                    except Exception:
                        logger.exception('Failed to send Get Involved notification email')

                return render(request, self.template, {
                    'page': self,
                    'form': None,
                    'submitted': True,
                })
        else:
            form = GetInvolvedForm()

        return render(request, self.template, {
            'page': self,
            'form': form,
            'submitted': False,
        })


# ── Donate Page ───────────────────────────────────────────────────────────────

class DonatePage(Page):
    template = 'a_home/donate_page.html'
    max_count = 1

    # Hero
    hero_eyebrow = models.CharField(max_length=80, blank=True)
    hero_title = models.CharField(max_length=200, blank=True)
    hero_intro = RichTextField(blank=True)

    # Why donate / impact cards
    why_title = models.CharField(max_length=120, blank=True)
    why_intro = RichTextField(blank=True)
    impact_cards = StreamField(
        [('card', DonationImpactCardBlock())],
        blank=True, use_json_field=True,
    )

    # How donations help (process steps)
    how_title = models.CharField(max_length=120, blank=True)
    how_intro = RichTextField(blank=True)
    how_steps = StreamField(
        [('step', DonationStepBlock())],
        blank=True, use_json_field=True,
    )

    # Trust & transparency
    trust_title = models.CharField(max_length=120, blank=True)
    trust_text = RichTextField(blank=True)
    abn_number = models.CharField(
        max_length=40, blank=True,
        help_text='Australian Business Number, e.g. "12 345 678 901".',
    )

    # FAQ
    faq_title = models.CharField(max_length=120, blank=True)
    faq_items = StreamField(
        [('faq', FAQBlock())],
        blank=True, use_json_field=True,
    )

    # Major gifts contact
    major_gifts_title = models.CharField(max_length=120, blank=True)
    major_gifts_text = RichTextField(blank=True)
    major_gifts_email = models.EmailField(blank=True)
    major_gifts_phone = models.CharField(max_length=50, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('hero_eyebrow'),
        index.SearchField('hero_title'),
        index.SearchField('hero_intro'),
        index.SearchField('why_title'),
        index.SearchField('why_intro'),
        index.SearchField('impact_cards'),
        index.SearchField('how_title'),
        index.SearchField('how_intro'),
        index.SearchField('how_steps'),
        index.SearchField('trust_title'),
        index.SearchField('trust_text'),
        index.SearchField('faq_title'),
        index.SearchField('faq_items'),
        index.SearchField('major_gifts_title'),
        index.SearchField('major_gifts_text'),
    ]

    parent_page_types = ['a_home.HomePage']
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_eyebrow'),
            FieldPanel('hero_title'),
            FieldPanel('hero_intro'),
        ], heading='Hero'),
        MultiFieldPanel([
            FieldPanel('why_title'),
            FieldPanel('why_intro'),
            FieldPanel('impact_cards'),
        ], heading='Why Donate'),
        MultiFieldPanel([
            FieldPanel('how_title'),
            FieldPanel('how_intro'),
            FieldPanel('how_steps'),
        ], heading='How Donations Help'),
        MultiFieldPanel([
            FieldPanel('trust_title'),
            FieldPanel('trust_text'),
            FieldPanel('abn_number'),
        ], heading='Trust & Transparency'),
        MultiFieldPanel([
            FieldPanel('faq_title'),
            FieldPanel('faq_items'),
        ], heading='FAQ'),
        MultiFieldPanel([
            FieldPanel('major_gifts_title'),
            FieldPanel('major_gifts_text'),
            FieldPanel('major_gifts_email'),
            FieldPanel('major_gifts_phone'),
        ], heading='Major Gifts'),
    ]

    class Meta:
        verbose_name = 'Donate Page'

    # ── Display properties ────────────────────────────────────────────────────

    @property
    def hero_eyebrow_display(self):
        return self.hero_eyebrow or 'Support CAWC NSW'

    @property
    def hero_title_display(self):
        return self.hero_title or 'Your contribution strengthens Cambodian families across NSW.'

    @property
    def hero_intro_display(self):
        return self.hero_intro or (
            '<p>Donations fund advocacy, culturally responsive programs, and practical '
            'support for seniors, women, children and newly arrived community members. '
            'Every contribution — large or small — helps the work continue.</p>'
        )

    @property
    def why_title_display(self):
        return self.why_title or 'Where your donation goes'

    @property
    def why_intro_display(self):
        return self.why_intro or (
            '<p>CAWC NSW operates with care and accountability. The majority of every '
            'dollar funds direct community work and culturally responsive support.</p>'
        )

    @property
    def impact_cards_display(self):
        if self.impact_cards:
            return [block.value for block in self.impact_cards]
        return [
            {
                'title': 'Community Programs',
                'description': (
                    "Cambodian Seniors Hub, Women's Support, Children's programs and "
                    "more — delivered in language and in culture."
                ),
                'amount_example': '$50 funds program materials for one session.',
            },
            {
                'title': 'Advocacy & Outreach',
                'description': (
                    'Helping community members access government services, navigate '
                    'settlement, and connect with culturally informed support.'
                ),
                'amount_example': '$100 supports a week of outreach contact.',
            },
            {
                'title': 'Cultural Connection',
                'description': (
                    'Cultural events, language preservation, and intergenerational '
                    'programs that keep heritage alive in NSW.'
                ),
                'amount_example': '$250 contributes to cultural event delivery.',
            },
        ]

    @property
    def how_title_display(self):
        return self.how_title or 'How your donation makes a difference'

    @property
    def how_intro_display(self):
        return self.how_intro or (
            '<p>From the moment you donate, your contribution moves directly into '
            'community-facing work.</p>'
        )

    @property
    def how_steps_display(self):
        if self.how_steps:
            return [block.value for block in self.how_steps]
        return [
            {'title': 'Direct community programs',
             'description': 'Funds go straight into running services for Cambodian families across NSW.'},
            {'title': 'Operational essentials',
             'description': 'Keeps program staff, venues and culturally informed delivery sustainable.'},
            {'title': 'Outreach & advocacy',
             'description': 'Supports community members to access services and navigate settlement.'},
            {'title': 'Long-term resilience',
             'description': 'Builds CAWC capacity to continue serving the community for decades.'},
        ]

    @property
    def trust_title_display(self):
        return self.trust_title or 'A registered, accountable charity'

    @property
    def trust_text_display(self):
        return self.trust_text or (
            '<p>CAWC NSW is a registered not-for-profit organisation with a community-elected '
            'board. We publish annual reports outlining how funds are used and the outcomes '
            'achieved across our programs.</p>'
        )

    @property
    def abn_display(self):
        return self.abn_number or 'Available on request'

    @property
    def faq_title_display(self):
        return self.faq_title or 'Common questions about donating'

    @property
    def faq_items_display(self):
        if self.faq_items:
            return [block.value for block in self.faq_items]
        # Fall back to shared FAQ snippets in the "donate" category
        try:
            from a_about.models import FAQ
            donate_faqs = FAQ.objects.filter(category='donate').order_by('sort_order', 'question')
            if donate_faqs.exists():
                return [
                    {'question': f.question, 'answer': f.answer}
                    for f in donate_faqs
                ]
        except Exception:
            pass
        return [
            {'question': 'Are donations tax-deductible?',
             'answer': '<p>CAWC NSW is a registered not-for-profit. Please check with our team for current tax-deductible status and to receive a receipt for your contribution.</p>'},
            {'question': 'Can I donate monthly?',
             'answer': '<p>Yes — choose the Monthly option in the donation form to set up a recurring contribution. You can adjust or cancel at any time.</p>'},
            {'question': 'Where can I see how funds are used?',
             'answer': '<p>Our annual reports detail program outcomes and financial summaries. Visit the Resources page to download them.</p>'},
            {'question': 'How do I make a major gift or corporate donation?',
             'answer': '<p>Get in touch with the team directly using the contact details below — we would love to talk about partnership and major gift opportunities.</p>'},
        ]

    @property
    def major_gifts_title_display(self):
        return self.major_gifts_title or 'Considering a major gift?'

    @property
    def major_gifts_text_display(self):
        return self.major_gifts_text or (
            '<p>For major gifts, corporate sponsorship, in-kind support, or partnership '
            'enquiries, please reach out to the CAWC NSW team directly.</p>'
        )

    @property
    def major_gifts_email_display(self):
        return self.major_gifts_email or 'cawcnsw@cambodianwelfare.org.au'

    @property
    def major_gifts_phone_display(self):
        return self.major_gifts_phone or '+61 2 9876 5432'


# ── Global organisation settings (used by footer, contact page, etc.) ────────

from wagtail.contrib.settings.models import BaseGenericSetting, register_setting


@register_setting(icon='site')
class OrganisationSettings(BaseGenericSetting):
    """Shared contact information used across the site (footer, contact page, meta)."""

    organisation_name = models.CharField(
        max_length=120,
        blank=True,
        default='CAWC NSW',
        help_text='Organisation name shown in the footer.',
    )
    phone_number = models.CharField(
        max_length=40,
        blank=True,
        default='+61 2 9727 4336',
        help_text='Main phone number. Used on the footer, contact page, and click-to-call links.',
    )
    email_address = models.EmailField(
        blank=True,
        default='cawcnsw@cambodianwelfare.org.au',
        help_text='Main contact email. Used on the footer, contact page, and click-to-email links.',
    )
    street_address = models.CharField(
        max_length=255,
        blank=True,
        default='Bonnyrigg Heights Community Centre',
        help_text='Street address shown on the contact page.',
    )
    suburb = models.CharField(
        max_length=120,
        blank=True,
        default='Bonnyrigg Heights NSW 2177',
        help_text='Suburb and postcode shown alongside the address.',
    )
    opening_hours = models.CharField(
        max_length=160,
        blank=True,
        default='Mon to Fri, 9:00am to 5:00pm',
        help_text='Office hours shown on the contact page.',
    )
    abn = models.CharField(
        max_length=40,
        blank=True,
        default='54 003 025 319',
        help_text='Australian Business Number. Shown in the footer legal bar.',
    )

    panels = [
        MultiFieldPanel([
            HelpPanel(
                'These details appear across the whole site — in the footer, on the contact page, '
                'and on click-to-call / click-to-email links. Update them once here and they will '
                'update everywhere automatically.'
            ),
            FieldPanel('organisation_name'),
            FieldPanel('phone_number'),
            FieldPanel('email_address'),
        ], heading='Contact'),
        MultiFieldPanel([
            FieldPanel('street_address'),
            FieldPanel('suburb'),
            FieldPanel('opening_hours'),
        ], heading='Location & Hours'),
        MultiFieldPanel([
            FieldPanel('abn'),
        ], heading='Legal'),
    ]

    class Meta:
        verbose_name = 'Organisation Settings'
