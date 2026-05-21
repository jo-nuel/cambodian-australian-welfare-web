from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_events', '0007_eventspage_facebook_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventspage',
            name='eyebrow',
            field=models.CharField(
                blank=True,
                default='Community Calendar',
                help_text='Small label above the page title (e.g. "Community Calendar").',
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name='eventspage',
            name='facebook_button_text',
            field=models.CharField(
                blank=True,
                default='View our events on Facebook',
                help_text='Label on the Facebook button.',
                max_length=80,
            ),
        ),
        migrations.AlterField(
            model_name='eventspage',
            name='intro',
            field=models.TextField(
                blank=True,
                default=(
                    'Our events are posted on Facebook. Follow us to stay up to date '
                    'with the latest programs, workshops, and community gatherings.'
                ),
                help_text='Description paragraph shown under the page title.',
            ),
        ),
    ]
