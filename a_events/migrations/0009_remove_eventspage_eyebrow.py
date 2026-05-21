from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('a_events', '0008_eventspage_editable_text_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventspage',
            name='eyebrow',
        ),
    ]
