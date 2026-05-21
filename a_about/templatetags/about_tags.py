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
    """Return '/km' when the active language is Khmer, else empty string.
    Use as: {% locale_prefix as lp %} then href="{{ lp }}{{ page.url }}"
    """
    from django.utils.translation import get_language
    return '/km' if (get_language() or 'en') == 'km' else ''


@register.simple_tag(takes_context=True)
def get_site_nav_pages(context):
    request = context.get('request')
    site = getattr(request, 'site', None) if request else None
    if not site:
        site = Site.objects.filter(is_default_site=True).select_related('root_page').first()
    if not site:
        return []
    # Always return English pages so nav labels are always in English.
    # The navbar template prefixes URLs with /km/ when in Khmer mode.
    return [
        page
        for page in site.root_page.get_children().live().public().specific()
        if page.slug not in EXCLUDED_SLUGS
    ]


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
