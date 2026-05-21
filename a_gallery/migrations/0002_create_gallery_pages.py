from django.db import migrations


def create_gallery_pages(apps, schema_editor):
    from wagtail.models import Page, Site
    from a_gallery.models import GalleryCategoryPage, GalleryImage, GalleryIndexPage
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page

    search_models = [GalleryIndexPage, GalleryCategoryPage, Page]
    for model in search_models:
        post_save.disconnect(post_save_signal_handler, sender=model)
    try:
        gallery_index = home.get_children().filter(slug="gallery").first()
        if gallery_index is not None:
            gallery_index = gallery_index.specific

        if not isinstance(gallery_index, GalleryIndexPage):
            gallery_index = GalleryIndexPage(
                title="Gallery",
                slug="gallery",
                intro_eyebrow="Photo Gallery",
                intro_title="Community, program, and event gallery",
                intro_text=(
                    "<p>A shared gallery for community life, program delivery, and CAWC NSW events. "
                    "Add images to the category pages in Wagtail and they will appear here automatically.</p>"
                ),
                show_in_menus=False,
            )
            home.add_child(instance=gallery_index)
            gallery_index.save_revision().publish()
        else:
            gallery_index.show_in_menus = False
            gallery_index.save_revision().publish()

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

        desired_slugs = {item[0] for item in desired_pages}

        for child in gallery_index.get_children().exclude(slug__in=desired_slugs):
            child.specific.delete()

        for slug, title, category, intro in desired_pages:
            page = gallery_index.get_children().filter(slug=slug).first()
            if page is not None:
                page = page.specific

            if not isinstance(page, GalleryCategoryPage):
                page = GalleryCategoryPage(
                    title=title,
                    slug=slug,
                    category=category,
                    intro=intro,
                    show_in_menus=False,
                )
                gallery_index.add_child(instance=page)
                page.save_revision().publish()
            else:
                page.title = title
                page.category = category
                page.show_in_menus = False
                if not page.intro:
                    page.intro = intro
                page.save_revision().publish()

            for grandchild in page.get_children():
                grandchild.specific.delete()

        GalleryImage.objects.all().delete()
    finally:
        for model in search_models:
            post_save.connect(post_save_signal_handler, sender=model)


class Migration(migrations.Migration):
    dependencies = [
        ("a_gallery", "0001_initial"),
        ("wagtailsearch", "0009_remove_ngram_autocomplete"),
    ]

    operations = [
        migrations.RunPython(create_gallery_pages, migrations.RunPython.noop),
    ]
