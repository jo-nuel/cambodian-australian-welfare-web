from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page, TranslatableMixin
from wagtail.search import index
from wagtail.snippets.models import register_snippet


class LinkBlock(blocks.StructBlock):
    text = blocks.CharBlock()
    link = blocks.CharBlock()


class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock()
    answer = blocks.RichTextBlock()


class StatBlock(blocks.StructBlock):
    value = blocks.CharBlock()
    label = blocks.CharBlock()
    description = blocks.CharBlock(required=False)


class FeatureItemBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    description = blocks.TextBlock()
    eyebrow = blocks.CharBlock(required=False)
    icon = blocks.CharBlock(required=False, help_text='Optional short icon label.')


class TimelineItemBlock(blocks.StructBlock):
    year = blocks.CharBlock()
    title = blocks.CharBlock(required=False)
    description = blocks.TextBlock()


class DirectorBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    name = blocks.CharBlock()
    role = blocks.CharBlock()
    bio = blocks.TextBlock(required=False)


STAFF_TEAM_CHOICES = [
    ('operations',  'Operations & Leadership'),
    ('settlement',  'Settlement & Casework'),
    ('seniors',     'Seniors Program'),
    ('women',       'Women & Family Support'),
    ('children',    'Children & Youth'),
    ('outreach',    'Community Outreach'),
    ('admin',       'Administration & Finance'),
    ('volunteers', 'Volunteers & Interns'),
]


class StaffMemberBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    name = blocks.CharBlock()
    role = blocks.CharBlock()
    team = blocks.ChoiceBlock(
        choices=STAFF_TEAM_CHOICES,
        required=False,
        help_text='Select the team this person belongs to. Staff with the same team are grouped together on the page.',
    )
    description = blocks.TextBlock(required=False)
    working_hours = blocks.CharBlock(required=False)
    focus = blocks.CharBlock(required=False, help_text='Optional program or area of responsibility.')


class AboutContentMixin:
    def _stream_values(self, field_name, block_type=None):
        stream = getattr(self, field_name, None)
        if not stream:
            return []
        if block_type:
            return [block.value for block in stream if block.block_type == block_type]
        return [block.value for block in stream]

    def _body_values(self, block_type):
        return self._stream_values('body', block_type)

    def _first_body_value(self, block_type):
        values = self._body_values(block_type)
        return values[0] if values else None

    @property
    def lead_heading_display(self):
        return self._first_body_value('heading') or self.title

    @property
    def lead_subheading_display(self):
        return self._first_body_value('subheading') or 'Community-led support for Cambodian families across NSW'

    @property
    def lead_paragraph_display(self):
        return self._first_body_value('paragraph') or (
            '<p>CAWC NSW is a community-led, not-for-profit organisation working to strengthen '
            'wellbeing, connection and opportunity for Cambodian communities across New South Wales.</p>'
        )

    @property
    def additional_paragraphs_display(self):
        paragraphs = self._body_values('paragraph')
        return paragraphs[1:] if len(paragraphs) > 1 else []

    @property
    def lead_image_display(self):
        lead_image = self._first_body_value('image')
        if lead_image:
            return lead_image
        image_text = self._first_body_value('image_text')
        if image_text:
            return image_text.get('image')
        return None

    @property
    def image_text_sections_display(self):
        return self._body_values('image_text')

    @property
    def gallery_images_display(self):
        galleries = []
        for group in self._body_values('carousel'):
            galleries.extend(group)
        return galleries

    @property
    def cta_buttons_display(self):
        return self._body_values('button')

    @property
    def primary_cta_display(self):
        buttons = self.cta_buttons_display
        if buttons:
            return buttons[0]
        return {'text': 'Explore Programs', 'link': '/programs/'}

    @property
    def secondary_cta_display(self):
        buttons = self.cta_buttons_display
        if len(buttons) > 1:
            return buttons[1]
        return None

    @property
    def stats_display(self):
        return self._stream_values('stats')

    @property
    def feature_items_display(self):
        return self._stream_values('feature_items')

    @property
    def timeline_items_display(self):
        return self._stream_values('timeline_items')

    @property
    def summary_display(self):
        summary_source = strip_tags(str(self.lead_paragraph_display))
        return Truncator(summary_source).chars(150)


class AboutIndexPage(AboutContentMixin, Page):
    page_heading = models.CharField(
        max_length=200,
        blank=True,
        help_text='Main heading shown at the top of the Who We Are page.',
    )
    page_intro = RichTextField(
        blank=True,
        help_text='Intro paragraph shown directly under the page heading.',
    )
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Large image shown below the hero. Landscape orientation works best.',
    )
    additional_text = RichTextField(
        blank=True,
        help_text='Supporting paragraphs shown in the "Community-led support" section. '
                  'Separate paragraphs are split automatically.',
    )

    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='title')),
        ('subheading', blocks.CharBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('image_text', blocks.StructBlock([
            ('image', ImageChooserBlock()),
            ('text', blocks.RichTextBlock()),
        ], label='Image with Text')),
        ('carousel', blocks.ListBlock(
            ImageChooserBlock(),
            label='Image Carousel',
        )),
        ('button', LinkBlock()),
    ], blank=True, use_json_field=True,
        help_text='Optional flexible content blocks. Use only if you need richer layouts than '
                  'the fields above offer.',
    )

    search_fields = Page.search_fields + [
        index.SearchField('page_heading'),
        index.SearchField('page_intro'),
        index.SearchField('additional_text'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                'These three fields control the top of the page. The hero image appears below '
                'the heading and intro paragraph.'
            ),
            FieldPanel('page_heading'),
            FieldPanel('page_intro'),
            FieldPanel('hero_image'),
        ], heading='Hero'),
        MultiFieldPanel([
            HelpPanel(
                'Paragraphs shown in the "Community-led support with cultural understanding" section, '
                'directly below the hero.'
            ),
            FieldPanel('additional_text'),
        ], heading='Supporting Paragraphs'),
        MultiFieldPanel([
            HelpPanel(
                'Optional advanced content. Only use this if you need richer layouts than the '
                'fields above offer — most editors should leave this blank.'
            ),
            FieldPanel('body'),
        ], heading='Advanced Content (optional)'),
    ]

    subpage_types = ['a_about.AboutSectionPage', 'a_about.BoardPage', 'a_about.StaffPage']

    class Meta:
        verbose_name = 'About Index Page'

    # ── Display properties — explicit fields take precedence over body ──

    @property
    def lead_heading_display(self):
        return self.page_heading or self._first_body_value('heading') or self.title

    @property
    def lead_paragraph_display(self):
        if self.page_intro:
            return self.page_intro
        return self._first_body_value('paragraph') or (
            '<p>CAWC NSW is a community-led, not-for-profit organisation working to strengthen '
            'wellbeing, connection and opportunity for Cambodian communities across New South Wales.</p>'
        )

    @property
    def additional_paragraphs_display(self):
        from django.utils.html import strip_tags
        if self.additional_text:
            # Split rich text on </p> for separate paragraph rendering
            raw = str(self.additional_text)
            chunks = [c.strip() for c in raw.split('</p>') if c.strip() and strip_tags(c).strip()]
            return [c + '</p>' if not c.endswith('</p>') else c for c in chunks]
        # Legacy fallback to body StreamField
        paragraphs = self._body_values('paragraph')
        return paragraphs[1:] if len(paragraphs) > 1 else []

    @property
    def hero_image_display(self):
        return self.hero_image or self.lead_image_display

    @property
    def section_cards_display(self):
        order = {
            'history': 0,
            'vision': 1,
            'mission': 2,
            'objectives': 3,
            'board': 4,
            'staff': 5,
        }
        children = []
        for child in self.get_children().live().public().specific():
            section_kind = getattr(child, 'section_kind', None)
            if child.slug in order or section_kind in {'history', 'vision', 'mission', 'objectives'}:
                children.append(child)
        return sorted(children, key=lambda child: (order.get(child.slug, 99), child.title.lower()))

    @property
    def mission_highlight_display(self):
        for child in self.section_cards_display:
            if getattr(child, 'section_kind', None) == 'mission':
                return child
        return None


class AboutSectionPage(AboutContentMixin, Page):
    SECTION_KIND_CHOICES = [
        ('standard', 'Standard'),
        ('history', 'History'),
        ('vision', 'Vision'),
        ('mission', 'Mission'),
        ('objectives', 'Objectives'),
    ]

    section_kind = models.CharField(
        max_length=20,
        choices=SECTION_KIND_CHOICES,
        default='standard',
        help_text='Controls the page layout. History = timeline of milestones. Vision/Mission = statement layout. Objectives = structured list. Standard = flexible content.',
    )
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='title')),
        ('subheading', blocks.CharBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('image_text', blocks.StructBlock([
            ('image', ImageChooserBlock()),
            ('text', blocks.RichTextBlock()),
        ], label='Image with Text')),
        ('carousel', blocks.ListBlock(
            ImageChooserBlock(),
            label='Image Carousel',
        )),
        ('button', LinkBlock()),
    ], blank=True, use_json_field=True)
    stats = StreamField([
        ('stat', StatBlock()),
    ], blank=True, use_json_field=True)
    timeline_items = StreamField([
        ('milestone', TimelineItemBlock()),
    ], blank=True, use_json_field=True)
    feature_items = StreamField([
        ('item', FeatureItemBlock()),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('stats'),
        index.SearchField('timeline_items'),
        index.SearchField('feature_items'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                '<strong>Start here.</strong> The section type controls how this page looks. '
                'Below, each section is labelled with which type uses it — fields not used by '
                'your chosen type will be ignored on the live page.<br><br>'
                '<strong>History</strong> — narrative page with stats and a timeline of milestones.<br>'
                '<strong>Vision</strong> — short statement page with an image.<br>'
                '<strong>Mission</strong> — statement page with feature cards.<br>'
                '<strong>Objectives</strong> — feature cards page listing focus areas.<br>'
                '<strong>Standard</strong> — fully flexible page using the Body StreamField only.'
            ),
            FieldPanel('section_kind'),
        ], heading='Section Type — start here'),
        MultiFieldPanel([
            HelpPanel(
                'The body StreamField is used as the <strong>main content</strong> for all section types. '
                'For History, Vision, Mission, and Objectives it provides the heading, subheading, and '
                'lead paragraph. For Standard, it is the only content field.'
            ),
            FieldPanel('body'),
        ], heading='Body — used by all section types'),
        MultiFieldPanel([
            HelpPanel(
                '<strong>Used by: History only.</strong> '
                'Statistics appear as large headline numbers below the body content.'
            ),
            FieldPanel('stats'),
        ], heading='Stats — History only (optional)'),
        MultiFieldPanel([
            HelpPanel(
                '<strong>Used by: History only.</strong> '
                'Add one milestone per entry (year + short description). They appear as a vertical timeline.'
            ),
            FieldPanel('timeline_items'),
        ], heading='Timeline Milestones — History only (optional)'),
        MultiFieldPanel([
            HelpPanel(
                '<strong>Used by: Mission and Objectives.</strong> '
                'Feature items appear as highlight cards below the body content.'
            ),
            FieldPanel('feature_items'),
        ], heading='Feature Items — Mission / Objectives only (optional)'),
    ]

    parent_page_types = ['a_about.AboutIndexPage']

    class Meta:
        verbose_name = 'About Section Page'


class BoardPage(Page):
    intro = RichTextField(blank=True)
    primary_cta_text = models.CharField(max_length=80, blank=True)
    primary_cta_link = models.CharField(max_length=255, blank=True)
    secondary_cta_text = models.CharField(max_length=80, blank=True)
    secondary_cta_link = models.CharField(max_length=255, blank=True)
    directors = StreamField([
        ('director', DirectorBlock(label='Director')),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('directors'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            HelpPanel('Add one entry per board member. Include a photo, their name, official role title, and a short bio.'),
            FieldPanel('directors'),
        ], heading='Board Members'),
        MultiFieldPanel([
            HelpPanel('Buttons shown at the bottom of the board page. Leave blank to use sensible defaults ("Support CAWC" and "Meet Our Staff").'),
            FieldPanel('primary_cta_text'),
            FieldPanel('primary_cta_link'),
            FieldPanel('secondary_cta_text'),
            FieldPanel('secondary_cta_link'),
        ], heading='Call To Action'),
    ]

    parent_page_types = ['a_about.AboutIndexPage']

    @property
    def intro_display(self):
        return self.intro or (
            'Meet the board members helping guide CAWC NSW with community knowledge, governance oversight '
            'and long-term commitment to culturally responsive support.'
        )

    @property
    def primary_cta_display(self):
        if self.primary_cta_text and self.primary_cta_link:
            return {'text': self.primary_cta_text, 'link': self.primary_cta_link}
        return {'text': 'Support CAWC', 'link': '/#donate'}

    @property
    def secondary_cta_display(self):
        if self.secondary_cta_text and self.secondary_cta_link:
            return {'text': self.secondary_cta_text, 'link': self.secondary_cta_link}
        return {'text': 'Meet Our Staff', 'link': '/about-us/staff/'}

    @property
    def summary_display(self):
        return 'Meet the board members supporting the organisation’s governance, direction and community accountability.'

    class Meta:
        verbose_name = 'Board of Directors Page'


class StaffPage(Page):
    intro = RichTextField(blank=True)
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    primary_cta_text = models.CharField(max_length=80, blank=True)
    primary_cta_link = models.CharField(max_length=255, blank=True)
    secondary_cta_text = models.CharField(max_length=80, blank=True)
    secondary_cta_link = models.CharField(max_length=255, blank=True)
    staff_members = StreamField([
        ('staff_member', StaffMemberBlock(label='Staff Member')),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('staff_members'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('featured_image'),
        FieldPanel('staff_members'),
        MultiFieldPanel([
            FieldPanel('primary_cta_text'),
            FieldPanel('primary_cta_link'),
            FieldPanel('secondary_cta_text'),
            FieldPanel('secondary_cta_link'),
        ], heading='Call To Action'),
    ]

    parent_page_types = ['a_about.AboutIndexPage']

    @property
    def intro_display(self):
        return self.intro or (
            'Meet the staff members supporting community programs, office coordination, settlement services '
            'and culturally responsive outreach across CAWC NSW.'
        )

    @property
    def primary_cta_display(self):
        if self.primary_cta_text and self.primary_cta_link:
            return {'text': self.primary_cta_text, 'link': self.primary_cta_link}
        return {'text': 'Explore Programs', 'link': '/programs/'}

    @property
    def secondary_cta_display(self):
        if self.secondary_cta_text and self.secondary_cta_link:
            return {'text': self.secondary_cta_text, 'link': self.secondary_cta_link}
        return {'text': 'See Community Events', 'link': '/events/'}

    @property
    def staff_groups_display(self):
        team_labels = dict(STAFF_TEAM_CHOICES)
        groups = []
        seen = {}
        members = [block.value for block in self.staff_members]
        for member in members:
            team_key = member.get('team') or 'operations'
            team_name = team_labels.get(team_key, team_key)
            if team_name not in seen:
                group = {'title': team_name, 'members': []}
                seen[team_name] = group
                groups.append(group)
            seen[team_name]['members'].append(member)
        return groups

    @property
    def summary_display(self):
        return 'Meet the staff members delivering projects, community support and day-to-day program coordination.'

    class Meta:
        verbose_name = 'Staff Page'


class FAQPage(Page):
    intro = RichTextField(blank=True)
    faqs = StreamField([
        ('faq', FAQItemBlock()),
    ], blank=True, use_json_field=True,
        help_text='Legacy local FAQs. New FAQs should be added under '
                  'Snippets → FAQs so they can be reused across pages.',
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('faqs'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                '<strong>This page automatically shows every FAQ snippet</strong> grouped by category. '
                'To add a new FAQ, go to <strong>Snippets → FAQs</strong> in the left sidebar and click '
                '<em>Add FAQ</em>. The FAQ will appear here automatically, and you can also choose to '
                'feature it on the homepage from the snippet edit screen.'
            ),
            FieldPanel('intro'),
        ], heading='Intro'),
        MultiFieldPanel([
            HelpPanel(
                'Legacy FAQs added on this page. We recommend migrating these to '
                'shared FAQ snippets so they can be reused. Leave blank to use only the snippet-based FAQs.'
            ),
            FieldPanel('faqs'),
        ], heading='Legacy FAQs (optional)'),
    ]

    class Meta:
        verbose_name = 'FAQ Page'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Group all FAQ snippets by category for display
        category_order = [key for key, label in FAQ_CATEGORY_CHOICES]
        all_faqs = FAQ.objects.all().order_by('sort_order', 'question')
        groups = []
        seen = {}
        category_labels = dict(FAQ_CATEGORY_CHOICES)
        for faq in all_faqs:
            label = category_labels.get(faq.category, faq.category.title())
            if label not in seen:
                group = {'title': label, 'items': []}
                seen[label] = group
                groups.append(group)
            seen[label]['items'].append(faq)
        
        groups.sort(key=lambda g: next(
            (i for i, (k, l) in enumerate(FAQ_CATEGORY_CHOICES) if l == g['title']),
            99
        ))
        context['faq_groups'] = groups
        return context

    @property
    def intro_display(self):
        return self.intro or (
            '<p>Find answers to common questions about CAWC NSW, our programs, how to get involved, '
            'and how to access our services.</p>'
        )


# ── Shared FAQ snippet — used across Home, FAQ, and Donate pages ─────────────

FAQ_CATEGORY_CHOICES = [
    ('general',  'General'),
    ('programs', 'Programs'),
    ('donate',   'Donations'),
    ('volunteer','Volunteering'),
    ('events',   'Events'),
    ('contact',  'Contact'),
]


@register_snippet
class FAQ(TranslatableMixin, models.Model):
    """A reusable FAQ question and answer.

    One FAQ can be referenced by multiple pages (Home, FAQ, Donate) without re-typing.
    Use the <em>category</em> field to control which FAQs appear on which page.
    """

    question = models.CharField(
        max_length=300,
        help_text='The question, e.g. "Are donations tax-deductible?"',
    )
    answer = RichTextField(
        help_text='The answer. Supports basic formatting and links.',
    )
    category = models.CharField(
        max_length=20,
        choices=FAQ_CATEGORY_CHOICES,
        default='general',
        help_text='Used to group FAQs and decide which pages they appear on. '
                  '"General" FAQs may appear on the homepage. '
                  '"Donations" FAQs appear on the Donate page. '
                  'All FAQs appear on the main FAQ page.',
    )
    sort_order = models.IntegerField(
        default=0,
        help_text='Lower numbers appear first within their category. Use 0, 10, 20 to leave room for reordering.',
    )
    show_on_homepage = models.BooleanField(
        default=False,
        help_text='Tick to feature this FAQ on the homepage (up to 4 are shown).',
    )

    panels = [
        FieldPanel('question'),
        FieldPanel('answer'),
        MultiFieldPanel([
            FieldPanel('category'),
            FieldPanel('sort_order'),
            FieldPanel('show_on_homepage'),
        ], heading='Where this FAQ appears'),
    ]

    search_fields = [
        index.SearchField('question'),
        index.SearchField('answer'),
        index.FilterField('category'),
        index.FilterField('show_on_homepage'),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ['category', 'sort_order', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
