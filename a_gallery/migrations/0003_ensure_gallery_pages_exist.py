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


def ensure_gallery_pages(apps, schema_editor):
    from wagtail.models import Page, Site
    from a_gallery.models import GalleryCategoryPage, GalleryIndexPage

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page

    search_models = [GalleryIndexPage, GalleryCategoryPage, Page]
    _disconnect_search(search_models)
    try:
        gallery = home.get_children().filter(slug="gallery").first()
        if gallery is not None:
            gallery = gallery.specific

        if gallery is None:
            gallery = GalleryIndexPage(
                title="Gallery",
                slug="gallery",
                intro_eyebrow="Photo Gallery",
                intro_title="Community, program, and event gallery",
                intro_text=(
                    "<p>A shared gallery for community life, program delivery, and CAWC NSW events. "
                    "Add images to the category pages in Wagtail and they will appear here automatically.</p>"
                ),
                show_in_menus=False,
                live=True,
            )
            home.add_child(instance=gallery)
            gallery.save_revision().publish()
        elif isinstance(gallery, GalleryIndexPage):
            gallery.show_in_menus = False
            gallery.save_revision().publish()
        else:
            return

        desired_pages = [
            (
                "community",
                "Community Photos",
                "community",
                "<p>Photos from community gatherings, volunteer moments, and the people who help shape CAWC NSW every week.</p>",
            ),
            (
                "programs",
                "Program Photos",
                "programs",
                "<p>Images from CAWC NSW program delivery, learning sessions, and practical support activities across the community.</p>",
            ),
            (
                "events",
                "Event Photos",
                "events",
                "<p>Moments from celebrations, information sessions, workshops, and other CAWC NSW events held throughout the year.</p>",
            ),
        ]

        for slug, title, category, intro in desired_pages:
            page = gallery.get_children().filter(slug=slug).first()
            if page is not None:
                page = page.specific

            if page is None:
                page = GalleryCategoryPage(
                    title=title,
                    slug=slug,
                    category=category,
                    intro=intro,
                    show_in_menus=False,
                    live=True,
                )
                gallery.add_child(instance=page)
                page.save_revision().publish()
            elif isinstance(page, GalleryCategoryPage):
                page.title = title
                page.category = category
                page.show_in_menus = False
                if not page.intro:
                    page.intro = intro
                page.save_revision().publish()
    finally:
        _reconnect_search(search_models)


class Migration(migrations.Migration):
    dependencies = [
        ("a_gallery", "0002_create_gallery_pages"),
        ("wagtailsearch", "0009_remove_ngram_autocomplete"),
    ]

    operations = [
        migrations.RunPython(ensure_gallery_pages, migrations.RunPython.noop),
    ]
