from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_events', '0006_remove_eventspage_categories_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventspage',
            name='facebook_url',
            field=models.URLField(
                blank=True,
                default='https://www.facebook.com/cambodianwelfare',
                help_text='Facebook page URL for the "View our events on Facebook" button.',
            ),
        ),
    ]
