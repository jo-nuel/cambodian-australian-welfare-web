# Handwritten migration — adds homepage redesign fields introduced in the
# approved CAWC homepage direction (intro, impact stats, featured programs,
# donation section title, volunteer image, community photo strip).

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_home', '0003_homepage_volunteer_cta_link_and_more'),
        ('wagtailimages', '0027_image_description'),
    ]

    operations = [
        # ── Introduction ──────────────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='intro_title',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='homepage',
            name='intro_text',
            field=wagtail.fields.RichTextField(blank=True),
        ),

        # ── Impact stats ──────────────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='impact_stats',
            field=wagtail.fields.StreamField(
                [('stat', 3)],
                blank=True,
                block_lookup={
                    0: ('wagtail.blocks.CharBlock', (), {
                        'help_text': 'Short metric, e.g. "100+", "1,200", "20 years".',
                        'max_length': 20,
                    }),
                    1: ('wagtail.blocks.CharBlock', (), {
                        'help_text': 'Metric label, e.g. "Active Volunteers".',
                    }),
                    2: ('wagtail.blocks.CharBlock', (), {
                        'help_text': 'Optional one-line supporting detail.',
                        'required': False,
                    }),
                    3: ('wagtail.blocks.StructBlock', [
                        [('value', 0), ('label', 1), ('description', 2)],
                    ], {}),
                },
            ),
        ),

        # ── Featured programs ─────────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='featured_programs',
            field=wagtail.fields.StreamField(
                [('program', 5)],
                blank=True,
                block_lookup={
                    0: ('wagtail.blocks.CharBlock', (), {}),
                    1: ('wagtail.blocks.TextBlock', (), {}),
                    2: ('wagtail.images.blocks.ImageChooserBlock', (), {'required': False}),
                    3: ('wagtail.blocks.CharBlock', (), {
                        'help_text': 'e.g. "Seniors Hub", "Women\'s Support".',
                        'required': False,
                    }),
                    4: ('wagtail.blocks.CharBlock', (), {
                        'help_text': 'Relative or absolute URL for this program page.',
                        'required': False,
                    }),
                    5: ('wagtail.blocks.StructBlock', [
                        [
                            ('title', 0),
                            ('summary', 1),
                            ('image', 2),
                            ('category', 3),
                            ('link', 4),
                        ],
                    ], {}),
                },
            ),
        ),

        # ── Donation section title ─────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='donation_section_title',
            field=models.CharField(blank=True, max_length=200),
        ),

        # ── Volunteer image ───────────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='volunteer_image',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='wagtailimages.image',
            ),
        ),

        # ── Community photo strip ─────────────────────────────────────────────
        migrations.AddField(
            model_name='homepage',
            name='photo_strip',
            field=wagtail.fields.StreamField(
                [('image', 0)],
                blank=True,
                block_lookup={
                    0: ('wagtail.images.blocks.ImageChooserBlock', (), {}),
                },
            ),
        ),
    ]
