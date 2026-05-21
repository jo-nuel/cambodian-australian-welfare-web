"""Tests for the Impact Records system.

Three invariants we want protected from future regressions:

1. Only one ImpactReportPeriod can be is_current=True at a time.
2. Records flagged display_on_impact_page=False never appear in the public
   page context.
3. The metrics CSV export never includes internal-only fields.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from wagtail.models import Locale

from .models import (
    ImpactAchievement,
    ImpactMetric,
    ImpactReportPeriod,
    ImpactStory,
)
from .wagtail_hooks import METRICS_EXPORT_COLUMNS, export_impact_metrics_csv


def _locale():
    locale, _ = Locale.objects.get_or_create(language_code='en')
    return locale


class IsCurrentUniquenessTests(TestCase):
    """ImpactReportPeriod.save() must demote any previously-current period
    when a new one is marked current. Without this guard, the public page
    can't decide which period to show."""

    def test_saving_a_new_current_period_demotes_the_old_one(self):
        locale = _locale()
        first = ImpactReportPeriod.objects.create(
            locale=locale, title='2024', is_current=True,
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
        )
        second = ImpactReportPeriod.objects.create(
            locale=locale, title='2025', is_current=True,
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31),
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_current)
        self.assertTrue(second.is_current)
        self.assertEqual(
            ImpactReportPeriod.objects.filter(is_current=True).count(),
            1,
        )

    def test_resaving_a_current_period_keeps_it_current(self):
        locale = _locale()
        period = ImpactReportPeriod.objects.create(
            locale=locale, title='2025', is_current=True,
        )

        # Edit something unrelated and save again.
        period.summary = 'Updated summary.'
        period.save()

        period.refresh_from_db()
        self.assertTrue(period.is_current)


class VisibilityFilteringTests(TestCase):
    """Records flagged display_on_impact_page=False must never reach the
    public Impact page context. Same for the homepage flag."""

    def setUp(self):
        self.locale = _locale()
        self.period = ImpactReportPeriod.objects.create(
            locale=self.locale, title='2025', is_current=True,
        )

        # Visible metric.
        self.public_metric = ImpactMetric.objects.create(
            locale=self.locale, title='Visible metric', value='100',
            category='programs', reporting_period=self.period,
            display_on_impact_page=True, display_on_homepage=True,
        )
        # Hidden metric — should never leak.
        self.internal_metric = ImpactMetric.objects.create(
            locale=self.locale, title='Internal only metric', value='999',
            category='programs', reporting_period=self.period,
            display_on_impact_page=False, display_on_homepage=False,
            internal_notes='Should never appear publicly.',
        )

        # Visible story.
        ImpactStory.objects.create(
            locale=self.locale, title='Visible story',
            category='community', reporting_period=self.period,
            display_on_impact_page=True,
        )
        # Hidden story.
        ImpactStory.objects.create(
            locale=self.locale, title='Internal only story',
            category='community', reporting_period=self.period,
            display_on_impact_page=False,
        )

        # Visible achievement.
        ImpactAchievement.objects.create(
            locale=self.locale, title='Visible achievement',
            category='other', reporting_period=self.period,
            display_on_impact_page=True,
        )
        # Hidden achievement.
        ImpactAchievement.objects.create(
            locale=self.locale, title='Internal only achievement',
            category='other', reporting_period=self.period,
            display_on_impact_page=False,
        )

    def _impact_page_context(self):
        from a_impact.models import ImpactPage
        page = ImpactPage(
            title='Impact', slug='impact-test',
            locale=self.locale,
        )
        # Skip tree placement — we only need get_context to run.
        rf = RequestFactory()
        return page.get_context(rf.get('/'))

    def test_hidden_metrics_are_not_in_context(self):
        ctx = self._impact_page_context()
        titles = [m.title for m in ctx['records_metrics']]
        self.assertIn('Visible metric', titles)
        self.assertNotIn('Internal only metric', titles)

    def test_hidden_stories_are_not_in_context(self):
        ctx = self._impact_page_context()
        titles = [s.title for s in ctx['records_stories']]
        self.assertIn('Visible story', titles)
        self.assertNotIn('Internal only story', titles)

    def test_hidden_achievements_are_not_in_context(self):
        ctx = self._impact_page_context()
        titles = [a.title for a in ctx['records_achievements']]
        self.assertIn('Visible achievement', titles)
        self.assertNotIn('Internal only achievement', titles)

    def test_homepage_filter_only_returns_flagged_metrics(self):
        ctx = self._impact_page_context()
        titles = [m.title for m in ctx['records_homepage_metrics']]
        self.assertEqual(titles, ['Visible metric'])

    def test_homepage_impact_stats_display_only_includes_homepage_flagged(self):
        from a_home.models import HomePage
        # A bare HomePage instance is enough — impact_stats_display reads from
        # the records system before falling back to its own StreamField.
        home = HomePage(title='Home', slug='home-test', locale=self.locale)
        labels = [s.get('label') for s in home.impact_stats_display]
        self.assertIn('Visible metric', labels)
        self.assertNotIn('Internal only metric', labels)


class CsvExportSafetyTests(TestCase):
    """Internal-only fields (internal_notes) must never end up in the CSV
    export. data_source is intentionally exported — it's an editorial source
    note, not a private note — but internal_notes is private."""

    def setUp(self):
        self.locale = _locale()
        self.period = ImpactReportPeriod.objects.create(
            locale=self.locale, title='2025', is_current=True,
        )
        ImpactMetric.objects.create(
            locale=self.locale, title='Metric one', value='100',
            category='programs', reporting_period=self.period,
            display_on_impact_page=True,
            internal_notes='SHOULD-NEVER-LEAK-internal-note',
        )

        User = get_user_model()
        self.staff = User.objects.create_user(
            username='staff', password='x', is_staff=True,
        )

    def test_internal_notes_never_appears_in_csv_response(self):
        rf = RequestFactory()
        req = rf.get(reverse('impact_metrics_export_csv'))
        req.user = self.staff
        resp = export_impact_metrics_csv(req)

        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b'SHOULD-NEVER-LEAK-internal-note', resp.content)
        self.assertNotIn(b'internal_notes', resp.content)

    def test_csv_column_list_excludes_internal_notes(self):
        self.assertNotIn('internal_notes', METRICS_EXPORT_COLUMNS)

    def test_unauthenticated_request_is_blocked(self):
        # Anonymous client must not reach the export. Wagtail's admin auth
        # middleware redirects to login (302) before our view-level check
        # (which would return 403) is even reached — either is acceptable
        # because both block access.
        client = Client()
        resp = client.get(reverse('impact_metrics_export_csv'))
        self.assertIn(resp.status_code, (302, 403))
        self.assertNotIn(b'SHOULD-NEVER-LEAK-internal-note', resp.content)
