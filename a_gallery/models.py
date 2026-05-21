from itertools import chain

from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


GALLERY_CATEGORY_CHOICES = [
    ("community", "Community"),
    ("programs", "Programs"),
    ("events", "Events"),
]

GALLERY_CATEGORY_ORDER = {
    "community": 0,
    "programs": 1,
    "events": 2,
}

GALLERY_CATEGORY_META = {
    "community": {
        "eyebrow": "Community Life",
        "intro": (
            "<p>Photos from community gatherings, volunteer moments, and the people who "
            "help shape CAWC NSW every week.</p>"
        ),
    },
    "programs": {
        "eyebrow": "Programs",
        "intro": (
            "<p>Images from CAWC NSW program delivery, learning sessions, and practical "
            "support activities across the community.</p>"
        ),
    },
    "events": {
        "eyebrow": "Events",
        "intro": (
            "<p>Moments from celebrations, information sessions, workshops, and other CAWC "
            "NSW events held throughout the year.</p>"
        ),
    },
}


class GalleryIndexPage(Page):
    template = "a_gallery/gallery_index_page.html"
    max_count = 1

    intro_eyebrow = models.CharField(max_length=120, blank=True)
    intro_title = models.CharField(max_length=200, blank=True)
    intro_text = RichTextField(blank=True)

    parent_page_types = ["a_home.HomePage"]
    subpage_types = ["a_gallery.GalleryCategoryPage"]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("intro_eyebrow"),
                FieldPanel("intro_title"),
                FieldPanel("intro_text"),
            ],
            heading="Intro",
        ),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro_eyebrow"),
        index.SearchField("intro_title"),
        index.SearchField("intro_text"),
    ]

    class Meta:
        verbose_name = "Gallery Overview Page"

    @property
    def intro_eyebrow_display(self):
        return self.intro_eyebrow or "Photo Gallery"

    @property
    def intro_title_display(self):
        return self.intro_title or "Community, program, and event gallery"

    @property
    def intro_text_display(self):
        return self.intro_text or (
            "<p>A shared gallery for community life, program delivery, and CAWC NSW events. "
            "Add images to the category pages in Wagtail and they will appear here automatically.</p>"
        )

    def _category_pages(self):
        return sorted(
            self.get_children().live().public().specific(),
            key=lambda page: GALLERY_CATEGORY_ORDER.get(getattr(page, "category", ""), 99),
        )

    def all_image_entries(self):
        return list(
            chain.from_iterable(
                getattr(page, "image_entries_display", []) for page in self._category_pages()
            )
        )

    @property
    def image_entries_display(self):
        return self.all_image_entries()

    def category_summary(self):
        """Return list of dicts: each category with its page, count, cover image."""
        summary = []
        for cat_page in self._category_pages():
            entries = getattr(cat_page, "image_entries_display", [])
            cover = entries[0].image if entries else None
            summary.append({
                "page": cat_page,
                "title": cat_page.title,
                "url": cat_page.url,
                "category": getattr(cat_page, "category", ""),
                "eyebrow": cat_page.category_meta["eyebrow"],
                "count": len(entries),
                "cover": cover,
            })
        return summary

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        active_category = (request.GET.get("category") or "").strip().lower()
        valid_categories = {key for key, _ in GALLERY_CATEGORY_CHOICES}

        all_entries = self.all_image_entries()
        if active_category and active_category in valid_categories:
            filtered = [e for e in all_entries if e.category == active_category]
        else:
            active_category = ""
            filtered = all_entries

        context["active_category"] = active_category
        context["filtered_entries"] = filtered
        context["total_count"] = len(all_entries)
        context["categories"] = self.category_summary()
        context["filter_chips"] = [
            {"label": "All photos", "value": "", "count": len(all_entries)},
        ] + [
            {
                "label": cat["title"],
                "value": cat["category"],
                "count": cat["count"],
            }
            for cat in context["categories"]
        ]
        return context


class GalleryCategoryPage(Page):
    template = "a_gallery/gallery_category_page.html"

    category = models.CharField(max_length=20, choices=GALLERY_CATEGORY_CHOICES, default="community")
    intro = RichTextField(blank=True)

    parent_page_types = ["a_gallery.GalleryIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("category"),
        FieldPanel("intro"),
        InlinePanel("gallery_images", label="Gallery Images"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("category"),
        index.SearchField("intro"),
        index.RelatedFields("gallery_images", [
            index.SearchField("category"),
            index.SearchField("caption"),
            index.SearchField("tag"),
        ]),
    ]

    class Meta:
        verbose_name = "Gallery Category Page"

    @property
    def category_meta(self):
        return GALLERY_CATEGORY_META.get(self.category, GALLERY_CATEGORY_META["community"])

    @property
    def intro_display(self):
        return self.intro or self.category_meta["intro"]

    @property
    def image_entries_display(self):
        return list(self.gallery_images.select_related("image", "related_page").order_by("sort_order", "id"))


class GalleryImage(Orderable):
    page = ParentalKey("a_gallery.GalleryCategoryPage", on_delete=models.CASCADE, related_name="gallery_images")
    category = models.CharField(max_length=20, choices=GALLERY_CATEGORY_CHOICES, default="community")
    caption = models.CharField(max_length=255, blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    related_page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    tag = models.CharField(max_length=80, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("tag"),
        FieldPanel("caption"),
        FieldPanel("related_page"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def save(self, *args, **kwargs):
        if self.page_id and self.category != self.page.category:
            self.category = self.page.category
        super().save(*args, **kwargs)

    @property
    def tag_display(self):
        if self.tag:
            return self.tag
        if self.related_page_id:
            return self.related_page.title
        if self.caption:
            return self.caption[:40]
        return "Photo"

    def __str__(self):
        return self.tag_display

