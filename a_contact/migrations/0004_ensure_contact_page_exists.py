from django.db import migrations


def _disconnect_search(models):
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler

    for model in models:
        post_save.disconnect(post_save_signal_handler, sender=model)


def _reconnect_search(models):
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler

    for model in models:
        post_save.connect(post_save_signal_handler, sender=model)


def ensure_contact_page(apps, schema_editor):
    from wagtail.models import Page, Site
    from a_contact.models import ContactPage

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page
    existing = home.get_children().filter(slug="contact").first()
    if existing is not None:
        existing = existing.specific
        if isinstance(existing, ContactPage):
            existing.show_in_menus = True
            existing.save_revision().publish()
        return

    search_models = [ContactPage, Page]
    _disconnect_search(search_models)
    try:
        page = ContactPage(
            title="Contact",
            slug="contact",
            show_in_menus=True,
            live=True,
        )
        home.add_child(instance=page)
        page.save_revision().publish()
    finally:
        _reconnect_search(search_models)


class Migration(migrations.Migration):
    dependencies = [
        ("a_contact", "0003_create_contact_page"),
        ("wagtailsearch", "0009_remove_ngram_autocomplete"),
    ]

    operations = [
        migrations.RunPython(ensure_contact_page, migrations.RunPython.noop),
    ]
