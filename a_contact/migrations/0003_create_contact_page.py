from django.db import migrations


def create_contact_page(apps, schema_editor):
    from wagtail.models import Page, Site
    from a_contact.models import ContactPage
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page
    if home.get_children().filter(slug="contact").exists():
        return

    search_models = [ContactPage, Page]
    for model in search_models:
        post_save.disconnect(post_save_signal_handler, sender=model)
    try:
        page = ContactPage(
            title="Contact",
            slug="contact",
            show_in_menus=True,
            live=True,
        )
        home.add_child(instance=page)
    finally:
        for model in search_models:
            post_save.connect(post_save_signal_handler, sender=model)


def reverse_contact_page(apps, schema_editor):
    from wagtail.models import Site

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    contact = site.root_page.get_children().filter(slug="contact").first()
    if contact is not None:
        contact.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("a_contact", "0002_contact_page_redesign"),
        ("a_home", "0007_getinvolvedsubmission"),
        ("wagtailsearch", "0009_remove_ngram_autocomplete"),
    ]

    operations = [
        migrations.RunPython(create_contact_page, reverse_contact_page),
    ]
