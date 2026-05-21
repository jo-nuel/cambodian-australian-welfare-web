import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("wagtailcore", "0096_referenceindex_referenceindex_source_object_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("body", wagtail.fields.StreamField([], blank=True)),
            ],
            options={
                "verbose_name": "Contact Page",
            },
            bases=("wagtailcore.page",),
        ),
    ]
