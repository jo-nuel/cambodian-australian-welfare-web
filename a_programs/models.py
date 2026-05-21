from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from wagtail.models import Page, TranslatableMixin
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index
from wagtail.snippets.models import register_snippet


# ── Program category snippet (editor-managed) ────────────────────────────────

@register_snippet
class ProgramCategory(TranslatableMixin, models.Model):
    """Editor-managed program category.

    Replaces the hardcoded PROGRAM_CATEGORY_CHOICES tuple so CAWC staff can add,
    rename, or reorder categories from Wagtail admin without developer involvement.
    """

    label = models.CharField(
        max_length=80,
        help_text='Display name shown on cards and the program page, e.g. "Seniors" or "Women & Families".',
    )
    sort_order = models.IntegerField(
        default=0,
        help_text='Lower numbers appear first in filter chips. Use 0, 10, 20 to leave room for reordering.',
    )

    panels = [
        FieldPanel('label'),
        FieldPanel('sort_order'),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ['sort_order', 'label']
        verbose_name = 'Program Category'
        verbose_name_plural = 'Program Categories'

    def __str__(self):
        return self.label


class ProgramsIndexPage(Page):
    intro = RichTextField(
        blank=True,
        help_text='Overview introduction shown at the top of the Programs page.',
    )
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Optional header image for the Programs overview page.',
    )

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('featured_image'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    subpage_types = ['a_programs.ProgramPage']

    class Meta:
        verbose_name = 'Programs Index Page'

    def get_context(self, request):
        context = super().get_context(request)
        programs = list(
            self.get_children()
            .live()
            .public()
            .specific()
            .order_by('title')
        )
        context['programs'] = programs
        context['program_count'] = len(programs)
        seen = set()
        cats = []
        for p in programs:
            key = p.category_key
            if key and key != 'other' and key not in seen:
                seen.add(key)
                cats.append({'key': key, 'label': p.category_display})
        context['program_categories'] = cats
        return context

    @property
    def intro_display(self):
        return self.intro or (
            '<p>CAWC NSW delivers a range of culturally responsive programs supporting Cambodian seniors, '
            'women, children, newly arrived migrants, older Laotian adults and families across New South Wales. '
            'Programs are designed to reduce isolation, improve wellbeing, strengthen cultural connection, '
            'and connect community members with services and support.</p>'
        )


PROGRAM_CATEGORY_CHOICES = [
    ('seniors',    'Seniors'),
    ('children',   'Children & Families'),
    ('women',      'Women & Families'),
    ('settlement', 'Settlement'),
    ('digital',    'Digital Safety'),
    ('social',     'Social Support'),
]


class ProgramPage(Page):
    category = models.CharField(
        max_length=50,
        choices=PROGRAM_CATEGORY_CHOICES,
        blank=True,
        help_text='Legacy fixed category. New programs should use "Category (snippet)" below instead.',
    )
    category_ref = models.ForeignKey(
        'a_programs.ProgramCategory',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Category',
        help_text='Pick a category from the list managed under Snippets → Program Categories. '
                  'If set, this overrides the legacy category field above.',
    )
    summary = models.CharField(
        max_length=300,
        blank=True,
        help_text='Short one-to-two sentence summary shown on program cards and in the overview grid.',
    )
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    outcomes = RichTextField(
        blank=True,
        help_text='Key results or impact highlights shown in the sidebar. Use a short bullet list.',
    )
    audience = RichTextField(
        blank=True,
        help_text='Who this program supports. Shown in a dedicated "Who it supports" section.',
    )
    schedule = models.CharField(
        max_length=200,
        blank=True,
        help_text='When the program runs, e.g. "Every Thursday 10am–12pm".',
    )
    venue = models.CharField(
        max_length=200,
        blank=True,
        help_text='Where the program is held.',
    )
    cost = models.CharField(
        max_length=100,
        blank=True,
        help_text='Cost to participants, e.g. "Free" or "By referral". Shown as a quick-scan pill.',
    )
    language = models.CharField(
        max_length=120,
        blank=True,
        help_text='Language(s) the program is delivered in, e.g. "Khmer and English".',
    )
    contact_name = models.CharField(max_length=120, blank=True,
        help_text='Program-specific contact person (optional).')
    contact_email = models.EmailField(blank=True,
        help_text='Program-specific contact email (optional).')
    contact_phone = models.CharField(max_length=40, blank=True,
        help_text='Program-specific contact phone (optional).')
    cta_heading = models.CharField(
        max_length=120,
        blank=True,
        help_text='Sidebar CTA card heading. Default: "Want to support this program?"',
    )
    gallery_note = models.CharField(
        max_length=300,
        blank=True,
        help_text='Optional "See more photos" callout text linking to the gallery.',
    )
    primary_cta_text = models.CharField(max_length=80, blank=True)
    primary_cta_link = models.CharField(max_length=255, blank=True)

    program_tag = models.CharField(
        max_length=100,
        blank=True,
        help_text='Tag used to filter gallery images for this program (e.g. cybersecurity)',
    )

    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='title')),
        ('subheading', blocks.CharBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('highlight_box', blocks.StructBlock([
            ('stat', blocks.CharBlock(
                label='Stat or key number',
                help_text='e.g. "90+" or "$3,000"',
            )),
            ('label', blocks.CharBlock(
                label='Label',
                help_text='e.g. "participants each week"',
            )),
            ('description', blocks.CharBlock(
                required=False,
                label='Supporting text (optional)',
            )),
        ], label='Highlight Box')),
        ('photo_grid', blocks.ListBlock(
            blocks.StructBlock([
                ('image', ImageChooserBlock()),
                ('caption', blocks.CharBlock(
                    required=False,
                    label='Caption (optional)',
                )),
            ]),
            label='Photo Grid',
        )),
        ('button', blocks.StructBlock([
            ('text', blocks.CharBlock()),
            ('link', blocks.CharBlock()),
        ])),
    ], blank=True, use_json_field=True)

    search_fields = Page.search_fields + [
        index.SearchField('category'),
        index.SearchField('summary'),
        index.SearchField('outcomes'),
        index.SearchField('audience'),
        index.SearchField('schedule'),
        index.SearchField('venue'),
        index.SearchField('cost'),
        index.SearchField('language'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                'Pick a category from the list managed under <strong>Snippets → Program Categories</strong>. '
                'To add a new category, go there and click "Add Program Category". '
                'The legacy "category" dropdown below is kept for backward compatibility — '
                'use the snippet-based one for new programs.'
            ),
            FieldPanel('category_ref'),
            FieldPanel('category'),
            FieldPanel('summary'),
            FieldPanel('featured_image'),
            FieldPanel('cost'),
            FieldPanel('language'),
        ], heading='Card / Overview'),
        MultiFieldPanel([
            FieldPanel('outcomes'),
            FieldPanel('audience'),
            FieldPanel('schedule'),
            FieldPanel('venue'),
        ], heading='Program Details'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('gallery_note'),
            FieldPanel('program_tag'),
        ], heading='Gallery'),
        MultiFieldPanel([
            FieldPanel('cta_heading'),
            FieldPanel('primary_cta_text'),
            FieldPanel('primary_cta_link'),
        ], heading='Call To Action'),
        MultiFieldPanel([
            FieldPanel('contact_name'),
            FieldPanel('contact_email'),
            FieldPanel('contact_phone'),
        ], heading='Program Contact (optional)'),
    ]

    parent_page_types = ['a_programs.ProgramsIndexPage']

    class Meta:
        verbose_name = 'Program Page'

    # ── Display helpers ──────────────────────────────────────────────────────

    @property
    def category_display(self):
        # Prefer the snippet-based category, fall back to the legacy choices field
        if self.category_ref_id and self.category_ref:
            return self.category_ref.label
        return dict(PROGRAM_CATEGORY_CHOICES).get(self.category, 'Community Program')

    @property
    def category_key(self):
        """Stable identifier used by filter chips on the programs index page."""
        if self.category_ref_id and self.category_ref:
            return f'cat-{self.category_ref_id}'
        return self.category or 'other'

    @property
    def summary_display(self):
        if self.summary:
            return self.summary
        # Auto-generate from first paragraph in body
        for block in self.body:
            if block.block_type == 'paragraph':
                raw = strip_tags(str(block.value))
                return Truncator(raw).chars(200)
        return ''

    @property
    def overview_subheading_display(self):
        blocks = list(self.body)
        if len(blocks) > 1 and blocks[1].block_type == 'subheading' and blocks[1].value:
            return str(blocks[1].value)
        return ''

    @property
    def overview_intro_display(self):
        for block in self.body:
            if block.block_type == 'paragraph' and block.value:
                return block.value
        return ''

    @property
    def detail_body_blocks(self):
        """Return body blocks after the opening editorial intro."""
        skipped = set()
        blocks = list(self.body)

        for index, block in enumerate(blocks):
            if block.block_type == 'heading':
                skipped.add(index)
                break

        if len(blocks) > 1 and blocks[1].block_type == 'subheading':
            skipped.add(1)

        for index, block in enumerate(blocks):
            if block.block_type == 'paragraph':
                skipped.add(index)
                break

        return [block for index, block in enumerate(blocks) if index not in skipped]

    @property
    def primary_cta_display(self):
        if self.primary_cta_text and self.primary_cta_link:
            return {'text': self.primary_cta_text, 'link': self.primary_cta_link}
        return {'text': 'Get Involved', 'link': '/get-involved/'}

    @property
    def audience_display(self):
        return self.audience or ''

    @property
    def schedule_display(self):
        return self.schedule or ''

    @property
    def venue_display(self):
        return self.venue or ''

    @property
    def gallery_note_display(self):
        return self.gallery_note or 'See more photos related to this project in our gallery.'

    @property
    def has_logistics(self):
        return bool(self.schedule or self.venue)

    @property
    def has_contact(self):
        return bool(self.contact_email or self.contact_phone)

    @property
    def cta_heading_display(self):
        return self.cta_heading or 'Want to support this program?'

    @property
    def has_at_a_glance(self):
        return bool(self.cost or self.language)
