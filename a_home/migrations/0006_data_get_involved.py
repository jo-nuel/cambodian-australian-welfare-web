"""
Data migration — replaces the old GetInvolvedIndexPage (a_involved app)
and its three subpages with a single GetInvolvedPage (a_home app).

On a fresh database the old page won't exist, so the migration simply
creates the new page.  On an existing database it deletes the old tree
and re-creates it as the merged single page.

Safe to run multiple times (idempotent slug check).
"""

from django.db import migrations


def _disconnect_search(models):
    """Disconnect modelsearch post_save signal for the given models."""
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler
    for model in models:
        post_save.disconnect(post_save_signal_handler, sender=model)


def _reconnect_search(models):
    from django.db.models.signals import post_save
    from modelsearch.signal_handlers import post_save_signal_handler
    for model in models:
        post_save.connect(post_save_signal_handler, sender=model)


def create_get_involved_page(apps, schema_editor):
    from wagtail.models import Page, Site
    from a_home.models import GetInvolvedPage

    try:
        site = Site.objects.get(is_default_site=True)
    except Site.DoesNotExist:
        return

    home = site.root_page

    # ── Clean up orphaned rows from the removed a_resources app ──────────────
    # PostgreSQL aborts the whole transaction on a failed statement even if
    # the exception is caught.  Use a savepoint so the rollback is scoped.
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SAVEPOINT sp_delete_resources")
        try:
            cursor.execute("DELETE FROM a_resources_volunteerpage")
            cursor.execute("RELEASE SAVEPOINT sp_delete_resources")
        except Exception:
            cursor.execute("ROLLBACK TO SAVEPOINT sp_delete_resources")

    # ── Remove old get-involved tree if present ───────────────────────────────
    old = home.get_children().filter(slug='get-involved').first()
    if old is not None:
        old.delete()

    old_vol = home.get_children().filter(slug='volunteer').first()
    if old_vol is not None:
        old_vol.delete()

    # ── Create merged GetInvolvedPage ─────────────────────────────────────────
    # Disconnect search signals so add_child doesn't depend on the search index
    # table existing during migrations. The index can be rebuilt post-deploy.
    search_models = [GetInvolvedPage, Page]
    _disconnect_search(search_models)
    try:
        page = GetInvolvedPage(
            title='Get Involved',
            slug='get-involved',
            show_in_menus=True,
            live=True,
        )
        home.add_child(instance=page)
    finally:
        _reconnect_search(search_models)


def reverse_get_involved_page(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('a_home', '0005_alter_homepage_support_cards_getinvolvedpage'),
        ('wagtailsearch', '0009_remove_ngram_autocomplete'),
    ]

    operations = [
        migrations.RunPython(
            create_get_involved_page,
            reverse_get_involved_page,
        ),
    ]
