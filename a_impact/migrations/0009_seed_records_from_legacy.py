"""Seed Impact Records from the legacy stat1/2/3 fields and add a small set of
clearly-labelled placeholder records so CAWC editors have a working example to
build from.

Every record this migration creates contains the marker string
"SEEDED-BY-MIGRATION-0009" in its internal_notes / data_source. The reverse
migration deletes only records with that marker, so editors can safely keep,
edit, or delete them without affecting their own work.
"""

import uuid
from datetime import date

from django.db import migrations


SEED_MARKER = 'SEEDED-BY-MIGRATION-0009'


def _english_locale_id(apps):
    Locale = apps.get_model('wagtailcore', 'Locale')
    locale = Locale.objects.filter(language_code='en').first()
    if locale is None:
        locale = Locale.objects.first()
    return locale.id if locale else None


def _make_translation_key():
    return uuid.uuid4()


def seed_impact_records(apps, schema_editor):
    ImpactPage = apps.get_model('a_impact', 'ImpactPage')
    ImpactReportPeriod = apps.get_model('a_impact', 'ImpactReportPeriod')
    ImpactMetric = apps.get_model('a_impact', 'ImpactMetric')
    ImpactStory = apps.get_model('a_impact', 'ImpactStory')
    ImpactAchievement = apps.get_model('a_impact', 'ImpactAchievement')

    # Skip seeding if any records already exist — never overwrite editor work.
    if (
        ImpactReportPeriod.objects.exists()
        or ImpactMetric.objects.exists()
        or ImpactStory.objects.exists()
        or ImpactAchievement.objects.exists()
    ):
        return

    locale_id = _english_locale_id(apps)
    if locale_id is None:
        # Wagtail not fully initialised yet; nothing safe to do.
        return

    # ── Current reporting period ────────────────────────────────────────────
    period = ImpactReportPeriod.objects.create(
        translation_key=_make_translation_key(),
        locale_id=locale_id,
        title='FY2025',
        period_type='fy',
        start_date=date(2024, 7, 1),
        end_date=date(2025, 6, 30),
        summary='Financial year 2024–2025 reporting period.',
        is_current=True,
        public_intro=(
            'A snapshot of the people, programs, and partnerships CAWC NSW '
            'supported across the 2024–2025 financial year.'
        ),
        internal_notes=(
            f'{SEED_MARKER} — placeholder period. Edit or delete once CAWC '
            'confirms the reporting cadence and real numbers.'
        ),
    )

    # ── Migrated headline metrics (from legacy stat1/2/3 fields) ────────────
    # Map: (value, title, category, unit, description)
    migrated = []
    for page in ImpactPage.objects.all():
        if page.stat1_number and page.stat1_label:
            migrated.append((page, 1, page.stat1_number, page.stat1_label))
        if page.stat2_number and page.stat2_label:
            migrated.append((page, 2, page.stat2_number, page.stat2_label))
        if page.stat3_number and page.stat3_label:
            migrated.append((page, 3, page.stat3_number, page.stat3_label))

    sort_order = 0
    for page, slot, value, label in migrated:
        ImpactMetric.objects.create(
            translation_key=_make_translation_key(),
            locale_id=locale_id,
            title=label,
            value=value,
            unit='',
            category='programs',
            reporting_period_id=period.id,
            description='',
            data_source=f'{SEED_MARKER} — migrated from ImpactPage.stat{slot}.',
            internal_notes=f'{SEED_MARKER} — migrated from the legacy stat fields.',
            display_on_impact_page=True,
            display_on_homepage=True,
            chart_enabled=False,
            sort_order=sort_order,
        )
        sort_order += 1

    # ── Placeholder metrics across categories (clearly labelled) ────────────
    placeholder_metrics = [
        {
            'title': 'Volunteer hours contributed',
            'value': '1,200',
            'unit': 'hours',
            'category': 'volunteers',
            'description': 'Hours given by volunteers across all CAWC programs.',
            'chart_enabled': True,
        },
        {
            'title': 'Cultural events hosted',
            'value': '14',
            'unit': 'events',
            'category': 'events',
            'description': 'Community gatherings, cultural celebrations, and information sessions.',
            'chart_enabled': True,
        },
        {
            'title': 'Settlement support sessions',
            'value': '320',
            'unit': 'sessions',
            'category': 'settlement',
            'description': 'One-on-one settlement and transition support sessions delivered.',
            'chart_enabled': True,
        },
        {
            'title': 'Donations received',
            'value': '85,000',
            'unit': 'dollars',
            'category': 'donations',
            'description': 'Generosity from community members, partners, and grant programs.',
            'chart_enabled': False,
            'display_on_homepage': True,
        },
    ]

    for meta in placeholder_metrics:
        ImpactMetric.objects.create(
            translation_key=_make_translation_key(),
            locale_id=locale_id,
            title=meta['title'],
            value=meta['value'],
            unit=meta['unit'],
            category=meta['category'],
            reporting_period_id=period.id,
            description=meta['description'],
            data_source=f'{SEED_MARKER} — placeholder figure.',
            internal_notes=(
                f'{SEED_MARKER} — placeholder metric. Replace with real CAWC data.'
            ),
            display_on_impact_page=True,
            display_on_homepage=meta.get('display_on_homepage', False),
            chart_enabled=meta.get('chart_enabled', False),
            sort_order=sort_order,
        )
        sort_order += 1

    # ── Placeholder stories ─────────────────────────────────────────────────
    placeholder_stories = [
        {
            'title': "A senior's story of connection",
            'summary': 'How a regular gathering at the Cambodian Seniors Hub became a lifeline.',
            'quote': 'I look forward to every Tuesday. It feels like family.',
            'category': 'community',
        },
        {
            'title': 'Settling in to a new chapter',
            'summary': 'A family\'s first year supported by CAWC\'s settlement program.',
            'quote': 'They walked with us through every step.',
            'category': 'settlement',
        },
    ]

    for sort_idx, story in enumerate(placeholder_stories):
        ImpactStory.objects.create(
            translation_key=_make_translation_key(),
            locale_id=locale_id,
            title=story['title'],
            summary=story['summary'],
            body='',
            quote=story['quote'],
            category=story['category'],
            reporting_period_id=period.id,
            display_on_impact_page=True,
            sort_order=sort_idx,
        )

    # ── Placeholder achievements ────────────────────────────────────────────
    placeholder_achievements = [
        {
            'title': 'New partnership with multicultural health service',
            'description': 'Joint outreach program covering three LGAs in Western Sydney.',
            'date': date(2024, 11, 15),
            'category': 'community',
        },
        {
            'title': 'Cyber Security for Vulnerable People grant secured',
            'description': 'Funding awarded to deliver digital safety workshops to seniors.',
            'date': date(2025, 2, 4),
            'category': 'programs',
        },
    ]

    for sort_idx, ach in enumerate(placeholder_achievements):
        ImpactAchievement.objects.create(
            translation_key=_make_translation_key(),
            locale_id=locale_id,
            title=ach['title'],
            description=ach['description'],
            date=ach['date'],
            category=ach['category'],
            reporting_period_id=period.id,
            display_on_impact_page=True,
            sort_order=sort_idx,
        )

    # ── Flip ImpactPage to use the records system ───────────────────────────
    ImpactPage.objects.filter(stat1_number__isnull=False).exclude(stat1_number='').update(
        use_records_system=True,
    )


def unseed_impact_records(apps, schema_editor):
    """Remove only records seeded by this migration (matched by marker)."""
    ImpactReportPeriod = apps.get_model('a_impact', 'ImpactReportPeriod')
    ImpactMetric = apps.get_model('a_impact', 'ImpactMetric')
    ImpactStory = apps.get_model('a_impact', 'ImpactStory')
    ImpactAchievement = apps.get_model('a_impact', 'ImpactAchievement')

    ImpactMetric.objects.filter(internal_notes__contains=SEED_MARKER).delete()
    ImpactAchievement.objects.filter(reporting_period__internal_notes__contains=SEED_MARKER).delete()
    ImpactStory.objects.filter(reporting_period__internal_notes__contains=SEED_MARKER).delete()
    ImpactReportPeriod.objects.filter(internal_notes__contains=SEED_MARKER).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('a_impact', '0008_impactpage_use_records_system'),
        # 0054 creates the default English Locale row that TranslatableMixin
        # records below rely on.
        ('wagtailcore', '0054_initial_locale'),
    ]

    operations = [
        migrations.RunPython(seed_impact_records, reverse_code=unseed_impact_records),
    ]
