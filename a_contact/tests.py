from django.test import TestCase
from wagtail.models import Site

from .models import ContactPage, ContactSubmission


class ContactPageTests(TestCase):
    def setUp(self):
        self.page = ContactPage.objects.live().first()
        self.assertIsNotNone(self.page)

    def test_contact_page_exists(self):
        self.assertEqual(self.page.slug, "contact")
        self.assertTrue(self.page.show_in_menus)

    def test_contact_page_renders(self):
        response = self.client.get(self.page.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send an enquiry")
        self.assertContains(response, "Visit")

    def test_contact_form_submission_creates_record(self):
        response = self.client.post(
            self.page.url,
            {
                "full_name": "Jamie Tester",
                "email": "jamie@example.com",
                "phone": "0400 000 000",
                "enquiry_area": "general",
                "message": "I would like more information about local support.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enquiry received")
        self.assertEqual(ContactSubmission.objects.count(), 1)
