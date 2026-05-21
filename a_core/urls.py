from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from django.urls import re_path
from .views import search_view
from .views_stripe import create_checkout_session, donation_success, donation_cancel, stripe_webhook
from a_resources.views import resource_download

from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

# Non-localised URLs (admin, payment webhooks, asset serving, etc.)
# These should NEVER live under a /km/ prefix.
urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('donate/checkout/', create_checkout_session, name='donate_checkout'),
    path('donate/webhook/', stripe_webhook, name='stripe_webhook'),
    path('resources/download/<str:resource_type>/<int:resource_id>/', resource_download, name='resource_download'),
    path('newsletter/', include('a_subscribers.urls')),
]

# Localised URLs — get a language prefix (/en/... or /km/...).
# prefix_default_language=False keeps English URLs unprefixed
# (e.g. /about/ stays as /about/, while Khmer becomes /km/about/).
urlpatterns += i18n_patterns(
    path('search/', search_view, name='search'),
    path('donate/success/', donation_success, name='donate_success'),
    path('donate/cancel/', donation_cancel, name='donate_cancel'),
    path('', include(wagtail_urls)),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Railway volumes are private filesystem mounts, so uploaded Wagtail media
    # needs an explicit route while the project is using volume-backed media.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
