from django.test import TestCase
from wagtail.models import Site

from .models import GalleryCategoryPage, GalleryIndexPage


class GalleryPageTests(TestCase):
    def test_gallery_pages_exist(self):
        site = Site.objects.get(is_default_site=True)

        gallery = GalleryIndexPage.objects.child_of(site.root_page).first()
        self.assertIsNotNone(gallery)

        categories = GalleryCategoryPage.objects.child_of(gallery).order_by("path")
        self.assertEqual(categories.count(), 3)
        self.assertEqual(
            list(categories.values_list("slug", flat=True)),
            ["community", "programs", "events"],
        )

    def test_gallery_routes_render(self):
        response = self.client.get("/gallery/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/gallery/programs/")
        self.assertEqual(response.status_code, 200)

