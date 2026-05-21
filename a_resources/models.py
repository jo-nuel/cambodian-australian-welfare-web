from django.db import models
from wagtail.models import Page, Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey
from wagtail.search import index


class AnnualReport(Orderable):
    page = ParentalKey('ResourcesPage', related_name='annual_reports', on_delete=models.CASCADE)
    year = models.IntegerField(help_text='Year the report covers, e.g. 2024.')
    url = models.URLField(blank=True, help_text='External link to the PDF or document. Leave blank if the report is not yet available — a placeholder will be shown.')

    panels = [
        FieldPanel('year'),
        FieldPanel('url'),
    ]

    def __str__(self):
        return f'Annual Report {self.year}'


class CommunityPublication(Orderable):
    page = ParentalKey('ResourcesPage', related_name='publications', on_delete=models.CASCADE)
    category = models.CharField(max_length=100, help_text='Group label, e.g. "Brochure", "Community Guide", "Newsletter". All entries with the same category are grouped together.')
    title = models.CharField(max_length=300, help_text='Publication title as it should appear to visitors.')
    url = models.URLField(blank=True, help_text='External link to the PDF or document. Leave blank if not yet available.')

    panels = [
        FieldPanel('category'),
        FieldPanel('title'),
        FieldPanel('url'),
    ]

    def __str__(self):
        return self.title


class UsefulLink(Orderable):
    page = ParentalKey('ResourcesPage', related_name='useful_links', on_delete=models.CASCADE)
    category = models.CharField(max_length=100, blank=True, help_text='Optional group label, e.g. "Government Services", "Health", "Legal Aid".')
    title = models.CharField(max_length=300, help_text='Link title as shown to visitors.')
    url = models.URLField(help_text='Full URL including https://')
    description = models.CharField(max_length=300, blank=True, help_text='Brief one-line description of what the link leads to.')

    panels = [
        FieldPanel('category'),
        FieldPanel('title'),
        FieldPanel('url'),
        FieldPanel('description'),
    ]

    def __str__(self):
        return self.title


class ResourceDownloadLead(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('annual-report', 'Annual Report'),
        ('publication', 'Community Publication'),
        ('useful-link', 'Useful Link'),
    ]

    email = models.EmailField()
    resource_type = models.CharField(max_length=40, choices=RESOURCE_TYPE_CHOICES)
    resource_title = models.CharField(max_length=300)
    resource_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Resource download lead'
        verbose_name_plural = 'Resource download leads'

    def __str__(self):
        return f'{self.email} - {self.resource_title}'


class ResourcesPage(Page):
    intro = models.TextField(
        blank=True,
        default=(
            'Access our archive of annual reports, community guides and organisational documents. '
            'We maintain these records to ensure transparency and provide cultural context for our work.'
        ),
    )

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        InlinePanel('annual_reports', label='Annual Reports'),
        InlinePanel('publications', label='Community Publications'),
        InlinePanel('useful_links', label='Useful Links'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.RelatedFields('annual_reports', [
            index.SearchField('year'),
            index.SearchField('url'),
        ]),
        index.RelatedFields('publications', [
            index.SearchField('category'),
            index.SearchField('title'),
            index.SearchField('url'),
        ]),
        index.RelatedFields('useful_links', [
            index.SearchField('category'),
            index.SearchField('title'),
            index.SearchField('description'),
            index.SearchField('url'),
        ]),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        reports = self.annual_reports.all().order_by('sort_order')
        context['reports'] = reports
        if reports.exists():
            years = list(reports.values_list('year', flat=True))
            context['newest_year'] = years[0]
            context['oldest_year'] = years[-1]
        context['publications'] = self.publications.all().order_by('sort_order')
        context['useful_links'] = self.useful_links.all().order_by('sort_order')
        return context

    class Meta:
        verbose_name = 'Resources Page'
