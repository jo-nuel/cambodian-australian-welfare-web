import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("a_contact", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactSubmission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("enquiry_area", models.CharField(max_length=80)),
                ("message", models.TextField()),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Contact Submission",
                "verbose_name_plural": "Contact Submissions",
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.AddField(
            model_name="contactpage",
            name="community_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="email_address",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="email_support_text",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="form_intro",
            field=wagtail.fields.RichTextField(blank=True),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="help_text",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="hero_title",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="intro",
            field=wagtail.fields.RichTextField(blank=True),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="location_address",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="location_name",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="location_suburb",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="location_support_text",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="opening_hours",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="phone_number",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="phone_support_text",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="contactpage",
            name="visit_intro",
            field=wagtail.fields.RichTextField(blank=True),
        ),
        migrations.RemoveField(
            model_name="contactpage",
            name="body",
        ),
    ]
