"""Admin wiring for the Impact Records system.

Snippets are registered with `add_to_admin_menu = False` so they don't appear
as top-level menu items. A single "Impacts" submenu sits alongside Subscribers
and contains Periods, Metrics, Stories, Achievements, and the CSV export.
"""

import csv
import io
import json
import uuid
from collections import Counter
from datetime import datetime

from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import path, reverse, reverse_lazy

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import (
    CATEGORY_CHOICES,
    ImpactAchievement,
    ImpactMetric,
    ImpactReportPeriod,
    ImpactStory,
)


# ── Permission helper ─────────────────────────────────────────────────────────

def _require_admin(request):
    """Return HttpResponseForbidden if user is not authenticated staff."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden()
    return None


# ── CSV export ────────────────────────────────────────────────────────────────

# Public-only columns. Internal-only fields (data_source, internal_notes) are
# deliberately excluded from the export to avoid leaking notes meant for staff.
METRICS_EXPORT_COLUMNS = [
    'period',
    'title',
    'value',
    'unit',
    'category',
    'related_program',
    'description',
    'data_source',
    'display_on_impact_page',
    'display_on_homepage',
    'chart_enabled',
    'chart_group',
    'sort_order',
    'created_at',
    'updated_at',
]


def export_impact_metrics_csv(request):
    if denied := _require_admin(request):
        return denied

    qs = ImpactMetric.objects.select_related('reporting_period', 'related_program').order_by(
        'reporting_period__start_date', 'sort_order', 'title',
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="cawc_impact_metrics_{datetime.now().strftime("%Y%m%d")}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(METRICS_EXPORT_COLUMNS)
    for m in qs:
        writer.writerow([
            m.reporting_period.title if m.reporting_period_id else '',
            m.title,
            m.value,
            m.get_unit_display() if m.unit else '',
            m.get_category_display(),
            m.related_program.title if m.related_program_id else '',
            m.description,
            m.data_source,
            m.display_on_impact_page,
            m.display_on_homepage,
            m.chart_enabled,
            m.chart_group,
            m.sort_order,
            m.created_at.isoformat(),
            m.updated_at.isoformat(),
        ])
    return response


# ── Import helpers ────────────────────────────────────────────────────────────

def _parse_value(raw):
    """Strip commas/spaces from numeric strings, return cleaned string."""
    if raw is None:
        return ''
    return str(raw).strip().replace(',', '').strip()


def _is_year(val):
    if val is None:
        return False
    # openpyxl may return datetime objects for year-formatted cells
    if hasattr(val, 'year'):
        return 1990 <= val.year <= 2100
    try:
        y = int(str(val).strip().split('-')[0].split('/')[0])
        return 1990 <= y <= 2100
    except (ValueError, TypeError):
        return False


def _parse_excel_style(rows):
    """Parse the CAWC multi-year column format:
    N | Indicator | 2025 | 2024 | 2023 | ... | Total
    Returns list of dicts: {period, title, value, errors}
    """
    if not rows:
        return []

    headers = [str(h).strip() for h in rows[0]]
    def _extract_year(raw_header):
        if hasattr(raw_header, 'year'):
            return raw_header.year
        return int(str(raw_header).strip().split('-')[0].split('/')[0])

    orig_headers = list(rows[0])
    year_cols = [(i, _extract_year(orig_headers[i]))
                 for i in range(len(orig_headers))
                 if _is_year(orig_headers[i])]

    if not year_cols:
        return []

    # Find indicator column (column 1 or named 'Indicator')
    indicator_col = 1
    for i, h in enumerate(headers):
        if 'indicator' in h.lower():
            indicator_col = i
            break

    records = []
    for row in rows[1:]:
        if not row or not any(str(c).strip() for c in row):
            continue
        title = str(row[indicator_col]).strip() if len(row) > indicator_col else ''
        if not title or title.lower() in ('total', 'n', '#'):
            continue
        for col_idx, year in year_cols:
            raw = row[col_idx] if len(row) > col_idx else ''
            cleaned = _parse_value(raw)
            if not cleaned or cleaned == '0':
                continue
            records.append({
                'period': str(year),
                'title': title,
                'value': cleaned,
                'unit': '',
                'category': 'programs',
                'description': '',
            })
    return records


def _parse_standard_csv(rows):
    """Parse our standard export format:
    period,title,value,unit,category,related_program,description,...
    """
    if not rows:
        return []
    # Use str() first — openpyxl cells can be None, csv.reader values are always str.
    headers = [str(h).lower().strip() if h is not None else '' for h in rows[0]]
    required = {'period', 'title', 'value'}
    if not required.issubset(set(headers)):
        return []

    records = []
    for row in rows[1:]:
        if not row:
            continue
        d = dict(zip(headers, row))
        title = str(d.get('title', '')).strip()
        period = str(d.get('period', '')).strip()
        value = _parse_value(d.get('value', ''))
        if not title or not period or not value:
            continue
        records.append({
            'period': period,
            'title': title,
            'value': value,
            'unit': str(d.get('unit', '')).strip(),
            'category': str(d.get('category', 'programs')).strip() or 'programs',
            'description': str(d.get('description', '')).strip(),
        })
    return records


def _read_upload(uploaded_file):
    """Read an uploaded .xlsx or .csv file and return (rows, error_string)."""
    name = uploaded_file.name.lower()
    if name.endswith('.xlsx') or name.endswith('.xls'):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(uploaded_file, data_only=True)
            ws = wb.active
            rows = [[cell.value for cell in row] for row in ws.iter_rows()]
            return rows, None
        except Exception as e:
            return [], f'Could not read Excel file: {e}'
    elif name.endswith('.csv'):
        try:
            content = uploaded_file.read().decode('utf-8-sig')
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            return rows, None
        except Exception as e:
            return [], f'Could not read CSV file: {e}'
    else:
        return [], 'Please upload a .xlsx or .csv file.'


def _detect_and_parse(rows):
    """Auto-detect format and parse rows into preview records."""
    if not rows:
        return [], 'File is empty.'
    headers = [str(h).strip() for h in rows[0] if h is not None]
    # Excel-style: has year numbers as column headers
    if any(_is_year(h) for h in headers):
        records = _parse_excel_style(rows)
    else:
        records = _parse_standard_csv(rows)
    if not records:
        return [], ('No metrics could be read. Check the file format. '
                    'Expected either the CAWC Excel format (year columns) '
                    'or the standard CSV format (period, title, value columns).')
    return records, None


# ── Import views ──────────────────────────────────────────────────────────────

def import_metrics(request):
    """Step 1 — upload file and show preview."""
    if denied := _require_admin(request):
        return denied

    error = None
    preview = None
    preview_json = None

    if request.method == 'POST' and 'confirm' not in request.POST:
        # File just uploaded — parse and show preview
        try:
            f = request.FILES.get('metrics_file')
            if not f:
                error = 'Please choose a file to upload.'
            else:
                rows, read_error = _read_upload(f)
                if read_error:
                    error = read_error
                else:
                    preview, parse_error = _detect_and_parse(rows)
                    if parse_error:
                        error = parse_error
                    else:
                        # Use ensure_ascii=True so JSON is safe for embedding in HTML
                        preview_json = json.dumps(preview, ensure_ascii=True)
        except Exception as e:
            error = f'Unexpected error reading file: {e}'

    elif request.method == 'POST' and 'confirm' in request.POST:
        # Confirmation step — save the metrics
        try:
            raw = request.POST.get('preview_json', '')
            try:
                records = json.loads(raw)
            except (ValueError, TypeError):
                error = 'Preview data was lost. Please upload the file again.'
                records = []

            if records:
                from wagtail.models import Locale
                from wagtail.admin import messages as wagtail_messages
                try:
                    locale = Locale.objects.get(language_code='en')
                except Locale.DoesNotExist:
                    locale = Locale.objects.first()

                created = 0
                skipped = 0
                for rec in records:
                    try:
                        period_title = str(rec.get('period', 'Unknown')).strip()
                        period, _ = ImpactReportPeriod.objects.get_or_create(
                            title=period_title,
                            locale=locale,
                            defaults={
                                'translation_key': uuid.uuid4(),
                                'period_type': 'year' if period_title.isdigit() else 'custom',
                                'internal_notes': 'Auto-created by CSV/Excel import.',
                            },
                        )
                        exists = ImpactMetric.objects.filter(
                            title=rec['title'],
                            reporting_period=period,
                            locale=locale,
                        ).exists()
                        if exists:
                            skipped += 1
                            continue
                        ImpactMetric.objects.create(
                            translation_key=uuid.uuid4(),
                            locale=locale,
                            title=rec['title'],
                            value=rec['value'],
                            unit=rec.get('unit', ''),
                            category=rec.get('category', 'programs') or 'programs',
                            description=rec.get('description', ''),
                            reporting_period=period,
                            display_on_impact_page=False,
                            display_on_homepage=False,
                            sort_order=0,
                            internal_notes='Imported via Excel/CSV import.',
                        )
                        created += 1
                    except Exception:
                        skipped += 1
                        continue

                if skipped and created == 0:
                    wagtail_messages.error(
                        request,
                        f'No metrics were imported — all {skipped} rows were skipped or already exist.'
                    )
                elif skipped:
                    wagtail_messages.warning(
                        request,
                        f'Imported {created} metric{"s" if created != 1 else ""}. '
                        f'{skipped} skipped (already exist or could not be saved).'
                    )
                else:
                    wagtail_messages.success(
                        request,
                        f'Successfully imported {created} metric{"s" if created != 1 else ""}. '
                        f'Go to Impact Metrics, review the list, and tick '
                        f'"Display on impact page" for the ones you want to show publicly.'
                    )
                return redirect(reverse('wagtailsnippets_a_impact_impactmetric:list'))
        except Exception as e:
            error = (
                f'Something went wrong while saving: {e}. '
                f'Please try uploading the file again or contact your developer.'
            )

    return render(request, 'a_impact/import_metrics.html', {
        'error': error,
        'preview': preview,
        'preview_json': preview_json,
    })


# ── Dashboard view ────────────────────────────────────────────────────────────

def impact_dashboard(request):
    if denied := _require_admin(request):
        return denied

    current_period = (
        ImpactReportPeriod.objects.filter(is_current=True).first()
        or ImpactReportPeriod.objects.order_by('-end_date', '-created_at').first()
    )

    # Totals (across all periods).
    total_periods = ImpactReportPeriod.objects.count()
    total_metrics = ImpactMetric.objects.count()
    total_metrics_public = ImpactMetric.objects.filter(display_on_impact_page=True).count()
    total_metrics_homepage = ImpactMetric.objects.filter(display_on_homepage=True).count()
    total_stories = ImpactStory.objects.count()
    total_achievements = ImpactAchievement.objects.count()

    # Data-quality warnings.
    metrics_missing_description = ImpactMetric.objects.filter(
        display_on_impact_page=True,
    ).filter(Q(description__isnull=True) | Q(description='')).count()
    metrics_missing_source = ImpactMetric.objects.filter(
        Q(data_source__isnull=True) | Q(data_source=''),
    ).count()

    # Metrics by category (count) — for the bar chart.
    category_counts_qs = (
        ImpactMetric.objects.values('category').annotate(count=Count('id')).order_by('-count')
    )
    category_label_map = dict(CATEGORY_CHOICES)
    max_cat_count = max((row['count'] for row in category_counts_qs), default=0)
    metrics_by_category = [
        {
            'key': row['category'],
            'label': category_label_map.get(row['category'], row['category']),
            'count': row['count'],
            'percent': round(row['count'] / max_cat_count * 100) if max_cat_count else 0,
        }
        for row in category_counts_qs
    ]

    # Metrics by period.
    period_counts_qs = (
        ImpactMetric.objects.values('reporting_period__title', 'reporting_period__id')
        .annotate(count=Count('id'))
        .order_by('-reporting_period__start_date')
    )
    max_period_count = max((row['count'] for row in period_counts_qs), default=0)
    metrics_by_period = [
        {
            'title': row['reporting_period__title'] or '(no period)',
            'count': row['count'],
            'percent': round(row['count'] / max_period_count * 100) if max_period_count else 0,
        }
        for row in period_counts_qs
    ]

    return render(request, 'a_impact/impact_dashboard.html', {
        'current_period': current_period,
        'total_periods': total_periods,
        'total_metrics': total_metrics,
        'total_metrics_public': total_metrics_public,
        'total_metrics_internal': total_metrics - total_metrics_public,
        'total_metrics_homepage': total_metrics_homepage,
        'total_stories': total_stories,
        'total_achievements': total_achievements,
        'metrics_missing_description': metrics_missing_description,
        'metrics_missing_source': metrics_missing_source,
        'metrics_by_category': metrics_by_category,
        'metrics_by_period': metrics_by_period,
    })


# ── Snippet view sets ─────────────────────────────────────────────────────────

class ImpactReportPeriodViewSet(SnippetViewSet):
    model = ImpactReportPeriod
    icon = 'date'
    menu_label = 'Impact Periods'
    menu_name = 'impact_periods'
    menu_order = 320
    add_to_admin_menu = False
    list_display = ['title', 'period_type', 'is_current', 'start_date', 'end_date', 'updated_at']
    list_filter = ['period_type', 'is_current']
    search_fields = ['title', 'summary']
    ordering = ['-start_date', '-created_at']
    list_per_page = 50


class ImpactMetricViewSet(SnippetViewSet):
    model = ImpactMetric
    icon = 'tablet-alt'
    menu_label = 'Impact Metrics'
    menu_name = 'impact_metrics'
    menu_order = 321
    add_to_admin_menu = False
    list_display = [
        'title', 'value', 'unit', 'category', 'reporting_period',
        'display_on_impact_page', 'display_on_homepage',
    ]
    list_filter = ['category', 'reporting_period', 'display_on_impact_page', 'display_on_homepage']
    search_fields = ['title', 'description']
    ordering = ['sort_order', '-updated_at']
    list_per_page = 50


class ImpactStoryViewSet(SnippetViewSet):
    model = ImpactStory
    icon = 'doc-full'
    menu_label = 'Impact Stories'
    menu_name = 'impact_stories'
    menu_order = 322
    add_to_admin_menu = False
    list_display = ['title', 'category', 'reporting_period', 'display_on_impact_page', 'updated_at']
    list_filter = ['category', 'reporting_period', 'display_on_impact_page']
    search_fields = ['title', 'summary']
    ordering = ['sort_order', '-updated_at']
    list_per_page = 50


class ImpactAchievementViewSet(SnippetViewSet):
    model = ImpactAchievement
    icon = 'pick'
    menu_label = 'Impact Achievements'
    menu_name = 'impact_achievements'
    menu_order = 323
    add_to_admin_menu = False
    list_display = ['title', 'category', 'date', 'reporting_period', 'display_on_impact_page']
    list_filter = ['category', 'reporting_period', 'display_on_impact_page']
    search_fields = ['title', 'description']
    ordering = ['sort_order', '-date']
    list_per_page = 50


register_snippet(ImpactReportPeriodViewSet)
register_snippet(ImpactMetricViewSet)
register_snippet(ImpactStoryViewSet)
register_snippet(ImpactAchievementViewSet)


# ── Admin URL & menu registration ─────────────────────────────────────────────

@hooks.register('register_admin_urls')
def register_impact_admin_urls():
    return [
        path('impact/dashboard/', impact_dashboard, name='impact_dashboard'),
        path('impact/import-metrics/', import_metrics, name='impact_metrics_import'),
        path(
            'impact/export-metrics-csv/',
            export_impact_metrics_csv,
            name='impact_metrics_export_csv',
        ),
    ]


# ── "Impacts" submenu ─────────────────────────────────────────────────────────
# Single top-level "Impacts" menu containing Periods, Metrics, Stories,
# Achievements, and the CSV export — sits alongside the Subscribers menu.

impacts_submenu = Menu(items=[
    MenuItem(
        'Impact Dashboard',
        reverse_lazy('impact_dashboard'),
        icon_name='chart-bar',
        order=5,
    ),
    MenuItem(
        'Impact Periods',
        reverse_lazy('wagtailsnippets_a_impact_impactreportperiod:list'),
        icon_name='date',
        order=10,
    ),
    MenuItem(
        'Impact Metrics',
        reverse_lazy('wagtailsnippets_a_impact_impactmetric:list'),
        icon_name='tablet-alt',
        order=20,
    ),
    MenuItem(
        'Impact Stories',
        reverse_lazy('wagtailsnippets_a_impact_impactstory:list'),
        icon_name='doc-full',
        order=30,
    ),
    MenuItem(
        'Impact Achievements',
        reverse_lazy('wagtailsnippets_a_impact_impactachievement:list'),
        icon_name='pick',
        order=40,
    ),
    MenuItem(
        'Import Metrics (Excel / CSV)',
        reverse_lazy('impact_metrics_import'),
        icon_name='upload',
        order=50,
    ),
    MenuItem(
        'Export Metrics CSV',
        reverse_lazy('impact_metrics_export_csv'),
        icon_name='download',
        order=60,
    ),
])


@hooks.register('register_admin_menu_item')
def register_impacts_submenu():
    return SubmenuMenuItem(
        'Impacts',
        impacts_submenu,
        icon_name='pick',
        order=320,
    )
