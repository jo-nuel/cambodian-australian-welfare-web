from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.html import strip_tags
from django.utils.text import Truncator
from wagtail.models import Page


PAGE_TYPE_LABELS = {
    'AboutIndexPage': 'Who We Are',
    'AboutSectionPage': 'Who We Are',
    'BoardPage': 'Who We Are',
    'StaffPage': 'Who We Are',
    'FAQPage': 'FAQ',
    'ProgramsIndexPage': 'Program',
    'ProgramPage': 'Program',
    'EventsPage': 'Event',
    'EventPage': 'Event',
    'ResourcesPage': 'Resource',
    'ContactPage': 'Contact',
    'DonatePage': 'Donate',
    'GetInvolvedPage': 'Get Involved',
    'ImpactPage': 'Impact',
    'GalleryIndexPage': 'Gallery',
    'GalleryCategoryPage': 'Gallery',
}

SEARCH_CATEGORIES = [
    {
        'key': 'programs',
        'label': 'Programs',
        'classes': {'ProgramsIndexPage', 'ProgramPage'},
    },
    {
        'key': 'events',
        'label': 'Events',
        'classes': {'EventsPage', 'EventPage'},
    },
    {
        'key': 'resources',
        'label': 'Resources',
        'classes': {'ResourcesPage'},
    },
    {
        'key': 'who-we-are',
        'label': 'Who We Are',
        'classes': {'AboutIndexPage', 'AboutSectionPage', 'BoardPage', 'StaffPage'},
    },
    {
        'key': 'impact',
        'label': 'Impact',
        'classes': {'ImpactPage'},
    },
    {
        'key': 'get-involved',
        'label': 'Get Involved',
        'classes': {'GetInvolvedPage', 'DonatePage'},
    },
    {
        'key': 'contact-faq',
        'label': 'Contact & FAQ',
        'classes': {'ContactPage', 'FAQPage'},
    },
    {
        'key': 'gallery',
        'label': 'Gallery',
        'classes': {'GalleryIndexPage', 'GalleryCategoryPage'},
    },
]


def _page_type_label(page):
    return PAGE_TYPE_LABELS.get(page.specific_class.__name__, page.specific_class._meta.verbose_name.title())


def _page_category_key(page):
    class_name = page.specific_class.__name__
    for category in SEARCH_CATEGORIES:
        if class_name in category['classes']:
            return category['key']
    return 'other'


def _page_summary(page):
    for attr in (
        'search_description',
        'summary_display',
        'summary',
        'intro_display',
        'intro',
        'hero_description',
    ):
        value = getattr(page, attr, '')
        if value:
            return Truncator(strip_tags(str(value))).chars(180)
    return 'Open this page to explore more details.'


def search_view(request):
    query = (request.GET.get('q') or '').strip()
    selected_categories = [
        category for category in request.GET.getlist('category')
        if category in {item['key'] for item in SEARCH_CATEGORIES}
    ]
    page_obj = None
    result_cards = []
    category_counts = {category['key']: 0 for category in SEARCH_CATEGORIES}

    if query:
        search_results = (
            Page.objects.live()
            .public()
            .exclude(depth=1)
            .search(query)
        )

        all_result_cards = []
        for result in search_results:
            page = result.specific
            category_key = _page_category_key(page)
            if category_key in category_counts:
                category_counts[category_key] += 1
            all_result_cards.append({
                'title': page.title,
                'url': page.url,
                'type': _page_type_label(page),
                'summary': _page_summary(page),
                'category': category_key,
            })

        filtered_cards = [
            card for card in all_result_cards
            if not selected_categories or card['category'] in selected_categories
        ]

        paginator = Paginator(filtered_cards, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        result_cards = list(page_obj.object_list)

    filter_options = [
        {
            'key': category['key'],
            'label': category['label'],
            'count': category_counts.get(category['key'], 0),
            'selected': category['key'] in selected_categories,
        }
        for category in SEARCH_CATEGORIES
    ]

    pagination_query = urlencode(
        {'q': query, 'category': selected_categories},
        doseq=True,
    )

    return render(
        request,
        'search.html',
        {
            'query': query,
            'results': result_cards,
            'page_obj': page_obj,
            'filter_options': filter_options,
            'selected_categories': selected_categories,
            'has_active_filters': bool(selected_categories),
            'pagination_query': pagination_query,
        },
    )
