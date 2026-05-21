from django.db import migrations


def ensure_donate_page(apps, schema_editor):
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler
    from wagtail.models import Page, Site

    from a_home.models import DonatePage

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page.specific
    existing = home.get_children().filter(slug='donate').first()

    post_save.disconnect(post_save_signal_handler, sender=DonatePage)
    post_save.disconnect(post_save_signal_handler, sender=Page)
    try:
        if existing is None:
            donate_page = DonatePage(
                title='Donate',
                slug='donate',
                show_in_menus=False,
                live=True,
            )
            home.add_child(instance=donate_page)
            donate_page.save_revision().publish()
        elif isinstance(existing.specific, DonatePage):
            donate_page = existing.specific
            donate_page.title = 'Donate'
            donate_page.show_in_menus = False
            donate_page.save_revision().publish()
    finally:
        post_save.connect(post_save_signal_handler, sender=DonatePage)
        post_save.connect(post_save_signal_handler, sender=Page)


class Migration(migrations.Migration):
    dependencies = [
        ('a_home', '0008_donatepage'),
        ('wagtailsearch', '0009_remove_ngram_autocomplete'),
    ]

    operations = [
        migrations.RunPython(ensure_donate_page, migrations.RunPython.noop),
    ]
