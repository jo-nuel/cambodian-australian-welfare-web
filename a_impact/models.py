from django.db import models
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page, TranslatableMixin
from wagtail.search import index


PERIOD_TYPE_CHOICES = [
    ('year', 'Year'),
    ('quarter', 'Quarter'),
    ('fy', 'Financial Year'),
    ('custom', 'Custom'),
]

CATEGORY_CHOICES = [
    ('programs', 'Programs'),
    ('events', 'Events'),
    ('volunteers', 'Volunteers'),
    ('donations', 'Donations'),
    ('community', 'Community Support'),
    ('settlement', 'Settlement'),
    ('other', 'Other'),
]

UNIT_CHOICES = [
    ('', '(none)'),
    ('people', 'people'),
    ('families', 'families'),
    ('sessions', 'sessions'),
    ('hours', 'hours'),
    ('dollars', 'dollars'),
    ('volunteers', 'volunteers'),
    ('events', 'events'),
]


class ImpactReportPeriod(TranslatableMixin, models.Model):
    """A reporting period (year, quarter, financial year) that groups metrics,
    stories, and achievements. Editors can flag one period as the current one
    used for public display."""

    title = models.CharField(
        max_length=100,
        help_text='e.g. "2025", "2025 Q1", "FY2025".',
    )
    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPE_CHOICES,
        default='year',
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    summary = models.TextField(
        blank=True,
        help_text='Short summary of this period. Optional.',
    )
    is_current = models.BooleanField(
        default=False,
        help_text='Mark this period as the current one used on the public Impact '
                  'page. Only one period can be current at a time.',
    )
    public_intro = models.TextField(
        blank=True,
        help_text='Intro paragraph shown on the public Impact page when this '
                  'period is current.',
    )
    internal_notes = models.TextField(
        blank=True,
        help_text='Internal-only notes. Never shown publicly.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            HelpPanel(
                'Define a reporting period. Metrics, stories, and achievements '
                'link back to a period for historical recordkeeping.'
            ),
            FieldPanel('title'),
            FieldPanel('period_type'),
            FieldPanel('start_date'),
            FieldPanel('end_date'),
            FieldPanel('summary'),
        ], heading='Period details'),
        MultiFieldPanel([
            HelpPanel(
                'Only one period can be marked current at a time. The public '
                'Impact page uses the current period by default.'
            ),
            FieldPanel('is_current'),
            FieldPanel('public_intro'),
        ], heading='Public display'),
        MultiFieldPanel([
            HelpPanel('Internal-only — never shown publicly.'),
            FieldPanel('internal_notes'),
        ], heading='Internal notes'),
    ]

    def save(self, *args, **kwargs):
        # Enforce only one current period at a time (across all locales).
        if self.is_current:
            ImpactReportPeriod.objects.exclude(pk=self.pk).filter(
                is_current=True,
            ).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta(TranslatableMixin.Meta):
        verbose_name = 'Impact Reporting Period'
        verbose_name_plural = 'Impact Reporting Periods'
        ordering = ['-start_date', '-created_at']


class ImpactMetric(TranslatableMixin, models.Model):
    """A single quantitative impact record (e.g. "1,200 families supported")."""

    title = models.CharField(
        max_length=200,
        help_text='What is being measured, e.g. "Families supported".',
    )
    value = models.CharField(
        max_length=50,
        help_text='Numeric or short text, e.g. "1,200", "200+", "20 years".',
    )
    unit = models.CharField(
        max_length=30,
        choices=UNIT_CHOICES,
        blank=True,
        help_text='Optional unit shown after the value.',
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='programs',
    )
    reporting_period = models.ForeignKey(
        'a_impact.ImpactReportPeriod',
        on_delete=models.PROTECT,
        related_name='metrics',
        help_text='Reporting period this metric belongs to.',
    )
    related_program = models.ForeignKey(
        'a_programs.ProgramPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Optional — link this metric to a specific program page.',
    )
    description = models.TextField(
        blank=True,
        help_text='Public explanation of what this metric represents. Shown '
                  'beneath the metric card on the public page.',
    )
    data_source = models.CharField(
        max_length=255,
        blank=True,
        help_text='Internal source note — never shown publicly. Encouraged for '
                  'accountability.',
    )
    internal_notes = models.TextField(
        blank=True,
        help_text='Internal-only notes. Never shown publicly.',
    )

    display_on_impact_page = models.BooleanField(
        default=False,
        help_text='Show this metric on the public Impact page.',
    )
    display_on_homepage = models.BooleanField(
        default=False,
        help_text='Show this metric in the homepage impact highlights.',
    )
    chart_enabled = models.BooleanField(
        default=False,
        help_text='Include this metric in chart sections (only used when enough '
                  'comparable metrics exist).',
    )
    chart_group = models.CharField(
        max_length=50,
        blank=True,
        help_text='Optional group name for grouping bars in the chart section.',
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            HelpPanel('Describe what is being measured.'),
            FieldPanel('title'),
            FieldPanel('value'),
            FieldPanel('unit'),
            FieldPanel('category'),
            FieldPanel('reporting_period'),
            FieldPanel('related_program'),
            FieldPanel('description'),
        ], heading='Metric'),
        MultiFieldPanel([
            HelpPanel(
                'Controls where this metric appears on the public site. '
                'Unticked metrics are kept as records but hidden from visitors.'
            ),
            FieldPanel('display_on_impact_page'),
            FieldPanel('display_on_homepage'),
            FieldPanel('chart_enabled'),
            FieldPanel('chart_group'),
            FieldPanel('sort_order'),
        ], heading='Visibility & display'),
        MultiFieldPanel([
            HelpPanel('Internal-only — never shown publicly.'),
            FieldPanel('data_source'),
            FieldPanel('internal_notes'),
        ], heading='Internal notes'),
    ]

    def __str__(self):
        if self.reporting_period_id:
            return f'{self.title} ({self.reporting_period.title})'
        return self.title

    class Meta(TranslatableMixin.Meta):
        verbose_name = 'Impact Metric'
        verbose_name_plural = 'Impact Metrics'
        ordering = ['sort_order', '-updated_at']


class ImpactStory(TranslatableMixin, models.Model):
    """A qualitative impact story or community outcome."""

    title = models.CharField(max_length=200)
    summary = models.CharField(
        max_length=300,
        blank=True,
        help_text='Short summary shown on cards and previews.',
    )
    body = RichTextField(
        blank=True,
        help_text='Full story body.',
    )
    quote = models.TextField(
        blank=True,
        help_text='Optional pull-quote highlighted on the public page.',
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='programs',
    )
    reporting_period = models.ForeignKey(
        'a_impact.ImpactReportPeriod',
        on_delete=models.PROTECT,
        related_name='stories',
    )
    related_program = models.ForeignKey(
        'a_programs.ProgramPage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    display_on_impact_page = models.BooleanField(
        default=False,
        help_text='Show this story on the public Impact page.',
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('summary'),
            FieldPanel('body'),
            FieldPanel('quote'),
            FieldPanel('image'),
            FieldPanel('category'),
            FieldPanel('reporting_period'),
            FieldPanel('related_program'),
        ], heading='Story'),
        MultiFieldPanel([
            HelpPanel('Controls where this story appears on the public site.'),
            FieldPanel('display_on_impact_page'),
            FieldPanel('sort_order'),
        ], heading='Visibility & display'),
    ]

    def __str__(self):
        return self.title

    class Meta(TranslatableMixin.Meta):
        verbose_name = 'Impact Story'
        verbose_name_plural = 'Impact Stories'
        ordering = ['sort_order', '-updated_at']


class ImpactAchievement(TranslatableMixin, models.Model):
    """A notable outcome, milestone, grant, partnership, or organisational
    achievement."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='other',
    )
    reporting_period = models.ForeignKey(
        'a_impact.ImpactReportPeriod',
        on_delete=models.PROTECT,
        related_name='achievements',
    )

    display_on_impact_page = models.BooleanField(
        default=False,
        help_text='Show this achievement on the public Impact page.',
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('description'),
            FieldPanel('date'),
            FieldPanel('category'),
            FieldPanel('reporting_period'),
        ], heading='Achievement'),
        MultiFieldPanel([
            HelpPanel('Controls where this achievement appears on the public site.'),
            FieldPanel('display_on_impact_page'),
            FieldPanel('sort_order'),
        ], heading='Visibility & display'),
    ]

    def __str__(self):
        return self.title

    class Meta(TranslatableMixin.Meta):
        verbose_name = 'Impact Achievement'
        verbose_name_plural = 'Impact Achievements'
        ordering = ['sort_order', '-date']


class ImpactPage(Page):
    template = 'a_impact/impact_page.html'

    # ── Hero ─────────────────────────────────────────────────────────────────
    subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text='Small eyebrow label shown above the hero heading. Used as a '
                  'fallback if the current reporting period has no public intro.',
    )
    intro_text = models.TextField(
        blank=True,
        help_text='Intro paragraph shown under the page title. Used as a '
                  'fallback if the current reporting period has no public intro.',
    )

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('intro_text'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            HelpPanel(
                'These fields appear at the very top of the Impact page. The '
                'subtitle is the small green label above the heading. The page '
                'body itself is sourced from the Impact Records system (Impacts → '
                'Periods / Metrics / Stories / Achievements).'
            ),
            FieldPanel('subtitle'),
            FieldPanel('intro_text'),
        ], heading='Hero'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Pick the current period, or fall back to the most recent by end_date
        # so the page never 500s on missing current flag.
        current_period = (
            ImpactReportPeriod.objects.filter(is_current=True).first()
            or ImpactReportPeriod.objects.order_by('-end_date', '-created_at').first()
        )

        metrics = []
        homepage_metrics = []
        stories = []
        achievements = []
        chart_metrics = []
        categories = []

        if current_period:
            metrics_qs = ImpactMetric.objects.filter(
                reporting_period=current_period,
                display_on_impact_page=True,
            ).order_by('sort_order', 'title')
            metrics = list(metrics_qs)

            homepage_metrics = list(
                ImpactMetric.objects.filter(
                    reporting_period=current_period,
                    display_on_homepage=True,
                ).order_by('sort_order', 'title')
            )

            stories = list(
                ImpactStory.objects.filter(
                    reporting_period=current_period,
                    display_on_impact_page=True,
                ).select_related('image').order_by('sort_order', '-updated_at')
            )

            achievements = list(
                ImpactAchievement.objects.filter(
                    reporting_period=current_period,
                    display_on_impact_page=True,
                ).order_by('sort_order', '-date')
            )

            chart_metrics = [m for m in metrics if m.chart_enabled]
            # Compute relative bar widths for the chart section. Skip metrics
            # whose value isn't parseable as a number — leave them at 0.
            def _numeric_value(raw):
                cleaned = ''.join(ch for ch in str(raw) if ch.isdigit() or ch == '.')
                try:
                    return float(cleaned) if cleaned else 0
                except ValueError:
                    return 0
            max_val = max((_numeric_value(m.value) for m in chart_metrics), default=0)
            for m in chart_metrics:
                v = _numeric_value(m.value)
                m.chart_percent = round(v / max_val * 100) if max_val else 0

            # Group metrics by category, preserving display order.
            seen = {}
            for m in metrics:
                seen.setdefault(m.category, {
                    'key': m.category,
                    'label': m.get_category_display(),
                    'metrics': [],
                })['metrics'].append(m)
            categories = list(seen.values())

        context.update({
            'current_period': current_period,
            'records_metrics': metrics,
            'records_homepage_metrics': homepage_metrics,
            'records_stories': stories,
            'records_achievements': achievements,
            'records_chart_metrics': chart_metrics if len(chart_metrics) >= 2 else [],
            'records_categories': categories if len(categories) >= 2 else [],
        })
        return context

    class Meta:
        verbose_name = 'Impact Page'
