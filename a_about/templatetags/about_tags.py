from django import template
from wagtail.models import Site
from a_about.models import AboutSectionPage, AboutIndexPage

register = template.Library()

EXCLUDED_SLUGS = {'gallery', 'contact', 'donate', 'faq'}


@register.simple_tag
def get_about_sections():
    return AboutSectionPage.objects.live().public()


@register.simple_tag
def locale_prefix():
    """Return '/km' when the active language is Khmer, else empty string."""
    from django.utils.translation import get_language
    return '/km' if (get_language() or 'en') == 'km' else ''


def _resolve_km_urls(pages_flat):
    """
    Given a flat list of English Page objects, batch-resolve their Khmer
    translated URLs using a single DB query (translation_key lookup).
    Sets page.resolved_url on each object.  Falls back to '/km' + page.url
    if no live Khmer translation exists.
    """
    from django.utils.translation import get_language
    from wagtail.models import Locale, Page as WagtailPage

    lang = get_language() or 'en'

    if lang != 'km':
        for p in pages_flat:
            p.resolved_url = p.url
        return

    try:
        km_locale = Locale.objects.get(language_code='km')
        keys = [p.translation_key for p in pages_flat]
        km_pages = WagtailPage.objects.filter(
            locale=km_locale,
            translation_key__in=keys,
        ).live()
        km_url_by_key = {str(p.translation_key): p.url for p in km_pages}

        for p in pages_flat:
            p.resolved_url = km_url_by_key.get(str(p.translation_key), '/km' + p.url)
    except Exception:
        for p in pages_flat:
            p.resolved_url = '/km' + p.url


@register.simple_tag(takes_context=True)
def get_site_nav_pages(context):
    request = context.get('request')
    site = getattr(request, 'site', None) if request else None
    if not site:
        site = Site.objects.filter(is_default_site=True).select_related('root_page').first()
    if not site:
        return []

    # Always use English pages so nav labels are always in English.
    en_pages = [
        page
        for page in site.root_page.get_children().live().public().specific()
        if page.slug not in EXCLUDED_SLUGS
    ]

    # Pre-fetch children and attach as nav_children so the template doesn't
    # call get_children() again (which would return fresh unmodified objects).
    all_pages_flat = []
    for page in en_pages:
        all_pages_flat.append(page)
        children = list(page.get_children().live().public())
        page.nav_children = children
        all_pages_flat.extend(children)

    # Batch-resolve locale-correct URLs (single extra query in Khmer mode).
    _resolve_km_urls(all_pages_flat)

    return en_pages


@register.simple_tag
def get_nav_extra_urls():
    """
    Return locale-correct URLs for the hardcoded nav items that are excluded
    from get_site_nav_pages: impact, resources, contact, gallery.
    In English mode returns /slug/; in Khmer mode resolves the actual Khmer
    page URL via translation_key (single batch query).
    """
    from django.utils.translation import get_language
    from wagtail.models import Locale, Page as WagtailPage

    SLUGS = ('impact', 'resources', 'contact', 'gallery')
    lang = get_language() or 'en'

    if lang != 'km':
        return {slug: f'/{slug}/' for slug in SLUGS}

    urls = {slug: f'/km/{slug}/' for slug in SLUGS}  # safe fallback
    try:
        en_locale = Locale.objects.get(language_code='en')
        km_locale = Locale.objects.get(language_code='km')
        en_pages = list(WagtailPage.objects.filter(slug__in=SLUGS, locale=en_locale))
        km_pages = WagtailPage.objects.filter(
            locale=km_locale,
            translation_key__in=[p.translation_key for p in en_pages],
        ).live()
        km_url_by_key = {str(p.translation_key): p.url for p in km_pages}
        for en_page in en_pages:
            km_url = km_url_by_key.get(str(en_page.translation_key))
            if km_url:
                urls[en_page.slug] = km_url
    except Exception:
        pass
    return urls


@register.simple_tag
def get_about_navigation_children():
    about_index = AboutIndexPage.objects.live().public().first()
    if not about_index:
        return []
    children = list(about_index.get_children().live().public().specific())
    order = {
        'history': 0,
        'vision': 1,
        'mission': 2,
        'objectives': 3,
        'board': 4,
        'staff': 5,
    }
    return sorted(children, key=lambda page: (order.get(page.slug, 99), page.title.lower()))
