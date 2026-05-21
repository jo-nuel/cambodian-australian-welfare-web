import re
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from wagtail.images import get_image_model

from a_about.models import BoardPage, StaffPage
from a_events.models import EventPage, EventsPage
from a_gallery.models import GalleryCategoryPage, GalleryImage
from a_home.models import HomePage
from a_programs.models import ProgramPage, ProgramsIndexPage


BOARD_IMAGE_MATCHES = {
    'Sarithya Tuy': ['sarithya'],
    'Nola Randall, OAM JP': ['nola'],
    'Lachlan Erskine': ['lachlan'],
    'Dara Sok': ['dara sok', 'dara_sok', 'dara-sok'],
    'Lisa Nagatsuka': ['lisa'],
    'Sophina Neang': ['sophina'],
    'Kim Chansreysor': ['kim chansreysor', 'kim_chansreysor', 'chansreysor'],
}

STAFF_IMAGE_MATCHES = {
    'Thin Em, JP': ['thin em'],
    'Ny Seng': ['ny seng'],
    'Rachana Bunn': ['rachana bunn'],
    'Chhun Y Ich': ['chhun'],
    'Y Hourng Kov': ['y hourng', 'hourng'],
    'Sok Chhin Chhai': ['sokk chhin', 'sok chhin'],
    'Sok Im Chhai': ['sok im chai', 'sok im chhai'],
    'Omethip Phommachanh': ['omethip'],
}

PROGRAM_IMAGE_RULES = {
    'cambodian-seniors-hub': ['senior hub'],
    'children-support-project': ['cambodian children support project'],
    'cyber-security': ['cyber security for vulnerable people'],
    'khmer-elderly-day-care': ['khmer elderly day care project'],
    'sets': ['settlement engagement and transition support program'],
    'women-support-hub': ['cambodian women support hub'],
}

EVENT_IMAGE_MATCHES = {
    'Harmony Day': ['harmony day', 'harmony'],
    'Refugee Week': ['refugee week', 'refugee'],
    'The NSW Settlement Partnership': ['settlement partnership', 'nsw settlement'],
    'Community Information Session': ['community information session', 'information session'],
    'Volunteer Welcome Day': ['volunteer welcome', 'volunteer'],
    'Women and Family Support Workshop': ['women family support workshop', 'women support', 'family support'],
}


class Command(BaseCommand):
    help = (
        'Attach already-uploaded Wagtail images to CAWC pages by matching image titles. '
        'Run with --apply to write changes; default is a dry run.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write changes to the database.')
        parser.add_argument(
            '--no-overwrite',
            action='store_true',
            help='Only fill empty image fields/blocks instead of replacing existing matches.',
        )
        parser.add_argument(
            '--clear-homepage-featured-programs',
            action='store_true',
            help='Clear manual Home Page featured program cards so the homepage uses live ProgramPage data.',
        )

    def handle(self, *args, **options):
        self.apply = options['apply']
        self.overwrite = not options['no_overwrite']
        self.images = self._load_image_index()

        self._attach_homepage_images(clear_featured_programs=options['clear_homepage_featured_programs'])
        self._attach_people_images(BoardPage, 'board', 'directors', 'director', BOARD_IMAGE_MATCHES)
        self._attach_people_images(StaffPage, 'staff', 'staff_members', 'staff_member', STAFF_IMAGE_MATCHES)
        self._attach_program_images()
        self._attach_event_images()
        self._attach_gallery_images()

        if not self.apply:
            self.stdout.write(self.style.WARNING('Dry run complete. Re-run with --apply to write these changes.'))

    def _load_image_index(self):
        image_model = get_image_model()
        images = list(image_model.objects.order_by('id'))
        index = {}
        for image in images:
            keys = {
                self._normalize(image.title),
                self._normalize(str(image.file.name).rsplit('/', 1)[-1].rsplit('.', 1)[0]),
            }
            for key in keys:
                if key:
                    index[key] = image
        self.stdout.write(f'Loaded {len(images)} uploaded Wagtail image record(s).')
        return index

    def _attach_homepage_images(self, clear_featured_programs=False):
        home = HomePage.objects.live().first()
        if not home:
            self.stdout.write(self.style.WARNING('No live Home Page found.'))
            return

        hero_image = self._find_image(['home-page-image', 'home page image', 'home page photo'])
        running_images = self._running_display_images()

        changed = False
        if hero_image and (self.overwrite or not home.hero_image_id):
            self._log(f'Home hero_image -> {hero_image.title}')
            if self.apply:
                home.hero_image = hero_image
            changed = True

        if running_images and (self.overwrite or not home.photo_strip):
            self._log(f'Home photo_strip -> {len(running_images)} running display image(s)')
            if self.apply:
                home.photo_strip = [
                    self._stream_item('image', image.pk)
                    for image in running_images
                ]
            changed = True

        if clear_featured_programs and home.featured_programs:
            self._log('Home featured_programs -> cleared so ProgramPage cards are used')
            if self.apply:
                home.featured_programs = []
            changed = True

        if changed and self.apply:
            home.save_revision().publish()

    def _attach_people_images(self, page_model, slug, stream_field, block_type, matches):
        page = page_model.objects.filter(slug=slug).first()
        if not page:
            self.stdout.write(self.style.WARNING(f'No {page_model.__name__} found at slug "{slug}".'))
            return

        raw_items = self._stream_raw_data(getattr(page, stream_field))
        changed = False
        for item in raw_items:
            if item.get('type') != block_type:
                continue
            value = item.setdefault('value', {})
            name = value.get('name', '')
            image = self._find_image(matches.get(name, []))
            if not image:
                self._log(f'{page.title}: no image match for {name}', warning=True)
                continue
            if value.get('image') and not self.overwrite:
                continue
            value['image'] = image.pk
            changed = True
            self._log(f'{page.title}: {name} -> {image.title}')

        if changed and self.apply:
            setattr(page, stream_field, raw_items)
            page.save_revision().publish()

    def _attach_program_images(self):
        index_page = ProgramsIndexPage.objects.live().first()
        if index_page:
            featured = self._find_image(['home page photo'])
            if featured and (self.overwrite or not index_page.featured_image_id):
                self._log(f'Programs overview featured_image -> {featured.title}')
                if self.apply:
                    index_page.featured_image = featured
                    index_page.save_revision().publish()

        for page in ProgramPage.objects.live().public():
            images = self._program_images(page.program_tag)
            if not images:
                self._log(f'{page.title}: no program image matches for tag "{page.program_tag}"', warning=True)
                continue

            raw_body = self._stream_raw_data(page.body)
            changed = False
            if self.overwrite or not page.featured_image_id:
                page.featured_image = images[0]
                changed = True
                self._log(f'{page.title}: featured_image -> {images[0].title}')

            if self.overwrite or not any(item.get('type') == 'carousel' for item in raw_body):
                raw_body = [item for item in raw_body if item.get('type') != 'carousel']
                raw_body.append(self._stream_item('carousel', [image.pk for image in images]))
                page.body = raw_body
                changed = True
                self._log(f'{page.title}: carousel -> {len(images)} image(s)')

            if changed and self.apply:
                page.save_revision().publish()

    def _attach_event_images(self):
        fallback_images = self._running_display_images()
        fallback_image = fallback_images[0] if fallback_images else self._find_image(['home-page-image', 'home page image'])

        events_index = EventsPage.objects.live().first()
        if events_index:
            changed = False
            if fallback_image and (self.overwrite or not events_index.featured_image_id):
                events_index.featured_image = fallback_image
                changed = True
                self._log(f'Events overview featured_image -> {fallback_image.title}')

            raw_cards = self._stream_raw_data(events_index.event_cards)
            for index, item in enumerate(raw_cards):
                if item.get('type') != 'event':
                    continue
                value = item.setdefault('value', {})
                if value.get('image') and not self.overwrite:
                    continue
                title = value.get('title', '')
                image = self._find_image(EVENT_IMAGE_MATCHES.get(title, []))
                if not image and fallback_images:
                    image = fallback_images[index % len(fallback_images)]
                if image:
                    value['image'] = image.pk
                    changed = True
                    self._log(f'Events legacy card "{title}" -> {image.title}')

            if changed and self.apply:
                events_index.event_cards = raw_cards
                events_index.save_revision().publish()

        fallback_index = 0
        for page in EventPage.objects.live().public():
            if page.featured_image_id and not self.overwrite:
                continue

            image = self._find_image(EVENT_IMAGE_MATCHES.get(page.title, []))
            if not image and fallback_images:
                image = fallback_images[fallback_index % len(fallback_images)]
                fallback_index += 1

            if image:
                self._log(f'{page.title}: featured_image -> {image.title}')
                if self.apply:
                    page.featured_image = image
                    page.save_revision().publish()
            else:
                self._log(f'{page.title}: no event image match found', warning=True)

    def _attach_gallery_images(self):
        program_gallery = GalleryCategoryPage.objects.filter(category='programs').live().first()
        if program_gallery:
            created = 0
            for page in ProgramPage.objects.live().public():
                for image in self._program_images(page.program_tag):
                    if GalleryImage.objects.filter(page=program_gallery, image=image).exists():
                        continue
                    created += 1
                    self._log(f'Program gallery: {image.title} -> {page.title}')
                    if self.apply:
                        GalleryImage.objects.create(
                            page=program_gallery,
                            image=image,
                            caption=image.title,
                            tag=page.program_tag,
                            related_page=page,
                        )
            if created:
                self.stdout.write(f'Program gallery entries to create: {created}')

        community_gallery = GalleryCategoryPage.objects.filter(category='community').live().first()
        if community_gallery:
            created = 0
            for image in self._running_display_images():
                if GalleryImage.objects.filter(page=community_gallery, image=image).exists():
                    continue
                created += 1
                self._log(f'Community gallery: {image.title}')
                if self.apply:
                    GalleryImage.objects.create(
                        page=community_gallery,
                        image=image,
                        caption=image.title,
                        tag='Community',
                    )
            if created:
                self.stdout.write(f'Community gallery entries to create: {created}')

    def _program_images(self, program_tag):
        needles = PROGRAM_IMAGE_RULES.get(program_tag, [])
        return self._images_containing(needles)

    def _running_display_images(self):
        image_model = get_image_model()
        candidates = []
        for image in image_model.objects.order_by('title', 'id'):
            key = self._normalize(image.title)
            filename_key = self._normalize(str(image.file.name).rsplit('/', 1)[-1])
            if (
                re.match(r'^\d{8}\s+\d+', key)
                or re.match(r'^\d{9,}\s+', key)
                or key.startswith('img 1391')
                or key.startswith('img 2450')
                or re.match(r'^\d{8}_\d+', filename_key)
                or re.match(r'^\d{9,}_', filename_key)
                or filename_key.startswith('img_1391')
                or filename_key.startswith('img_2450')
            ):
                candidates.append(image)
        return candidates

    def _images_containing(self, needles):
        image_model = get_image_model()
        matches = []
        normalized_needles = [self._normalize(needle) for needle in needles]
        for image in image_model.objects.order_by('title', 'id'):
            haystacks = [
                self._normalize(image.title),
                self._normalize(str(image.file.name).rsplit('/', 1)[-1]),
            ]
            if any(needle and any(needle in haystack for haystack in haystacks) for needle in normalized_needles):
                matches.append(image)
        return matches

    def _find_image(self, candidates):
        for candidate in candidates:
            key = self._normalize(candidate)
            image = self.images.get(key)
            if image:
                return image
        return None

    def _stream_raw_data(self, stream_value):
        raw_data = getattr(stream_value, 'raw_data', None)
        if raw_data is not None:
            return [self._normalize_stream_item(item) for item in raw_data]

        data = []
        for block in stream_value:
            value = block.value
            if hasattr(value, 'items'):
                value = dict(value)
                image = value.get('image')
                if hasattr(image, 'pk'):
                    value['image'] = image.pk
            data.append(self._stream_item(block.block_type, value))
        return data

    def _normalize_stream_item(self, item):
        normalized = {
            'type': item.get('type'),
            'value': item.get('value'),
            'id': item.get('id') or str(uuid4()),
        }
        return normalized

    def _stream_item(self, block_type, value):
        return {
            'type': block_type,
            'value': value,
            'id': str(uuid4()),
        }

    def _normalize(self, value):
        value = str(value or '').rsplit('.', 1)[0]
        return slugify(value).replace('-', ' ').strip().lower()

    def _log(self, message, warning=False):
        if warning:
            self.stdout.write(self.style.WARNING(message))
        else:
            self.stdout.write(message)
