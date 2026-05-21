"""
Seed script — populates the database with initial site data.
Run with: uv run python manage.py shell < seed.py
"""
import django
django.setup()

from django.core.files.base import ContentFile
from wagtail.models import Page, Site
from wagtail.images.models import Image
from a_about.models import AboutIndexPage, AboutSectionPage, BoardPage, StaffPage
from a_events.models import EventsPage
from a_home.models import DonatePage, GetInvolvedPage, HomePage
from a_programs.models import ProgramsIndexPage, ProgramPage
from a_resources.models import AnnualReport, CommunityPublication, ResourcesPage

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_or_create_image(title, filename):
    """Load an image from media/seed_images/ into the Wagtail image library."""
    import os
    from django.conf import settings

    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing

    seed_path = os.path.join(settings.BASE_DIR, 'media', 'seed_images', filename)
    if not os.path.exists(seed_path):
        print(f'  [warn] Seed image not found: {seed_path} - skipping image')
        return None

    from PIL import Image as PILImage
    import io
    from django.core.files.storage import default_storage

    with open(seed_path, 'rb') as f:
        content = f.read()

    # PIL's full open() supports AVIF; Django's incremental parser (used by
    # update_dimension_fields) does not — so we get dimensions here directly.
    pil_img = PILImage.open(io.BytesIO(content))
    pil_img.load()
    width, height = pil_img.size

    # Save file to storage directly (bypasses ImageField descriptor which would
    # call get_image_dimensions() via the incremental parser and return None).
    saved_path = default_storage.save(f'original_images/{filename}', ContentFile(content))

    # Create the record with a string path — descriptor treats it as committed
    # and does not call update_dimension_fields, so our width/height are kept.
    image = Image.objects.create(title=title, file=saved_path, width=width, height=height)
    print(f'  [ok] Created image: {title}')
    return image


def clean_slate():
    """Remove all non-root pages so we can re-seed cleanly."""
    root = Page.objects.get(depth=1)
    for child in root.get_children():
        child.delete()
    root.refresh_from_db()
    root.numchild = root.get_children().count()
    root.save(update_fields=['numchild'])
    Site.objects.all().delete()
    Image.objects.all().delete()
    print('[ok] Cleared existing pages, sites and images')


# ── Seed ─────────────────────────────────────────────────────────────────────

clean_slate()

root = Page.objects.get(depth=1)

# Home Page
home = HomePage(
    title='Home Page',
    slug='home',
    hero_eyebrow='Community-led support since 1983',
    hero_title='Supporting Cambodian families and communities across NSW',
    hero_description='CAWC NSW is a community-led not-for-profit established to support Cambodian Australians through culturally responsive programs, advocacy, settlement support, events and practical pathways to connection.',
    primary_cta_text='Donate Now',
    primary_cta_link='/#donate',
    secondary_cta_text='View Programs',
    secondary_cta_link='/programs/',
    intro_title='A trusted community connection point',
    intro_text=(
        '<p>The Cambodian-Australian Welfare Council of NSW Inc. supports Cambodian '
        'families, seniors, women, children and newly arrived community members across '
        'New South Wales. Originally established in 1983 as Khmer Interagency, CAWC '
        'continues to promote wellbeing, cultural connection, access to services and '
        'participation in Australian community life.</p>'
    ),
    impact_stats=[
        ('stat', {
            'value': '1983',
            'label': 'Established',
            'description': 'Founded as Khmer Interagency by workers supporting Khmer communities.',
        }),
        ('stat', {
            'value': '1996',
            'label': 'Incorporated',
            'description': 'Formalised as the Cambodian-Australian Welfare Council of NSW Inc.',
        }),
        ('stat', {
            'value': '7',
            'label': 'Core Objectives',
            'description': 'Guiding culture, service access, community harmony and advocacy.',
        }),
    ],
    featured_programs=[
        ('program', {
            'title': 'Cambodian Seniors Hub',
            'summary': 'A regular safe space for Cambodian seniors to connect, share morning tea, take part in gentle activities and learn about local services.',
            'image': None,
            'category': 'Seniors',
            'link': '/programs/cambodian-seniors-hub/',
        }),
        ('program', {
            'title': 'Settlement Engagement and Transition Support',
            'summary': 'Support for eligible humanitarian entrants and newly arrived Cambodian migrants as they build independence, confidence and community connection.',
            'image': None,
            'category': 'Settlement',
            'link': '/programs/settlement-engagement-and-transition-support-program-sets/',
        }),
        ('program', {
            'title': 'Cambodian Children Support Project',
            'summary': 'Homework help, tutoring and school holiday activities that support confidence, literacy, numeracy and school transition for Cambodian children.',
            'image': None,
            'category': 'Children and families',
            'link': '/programs/cambodian-children-support-project/',
        }),
    ],
    upcoming_events_intro='Explore community sessions, workshops and cultural activities that help people connect, learn and access support.',
    upcoming_events=[
        ('event', {
            'date': '2026-06-04',
            'title': 'Community Information Session',
            'location': 'Fairfield, NSW',
            'description': 'A welcoming session for sharing local service information, referrals and practical community support.',
            'cta_text': 'View details',
            'cta_link': '/events/',
        }),
        ('event', {
            'date': '2026-06-18',
            'title': 'Volunteer Welcome Day',
            'location': 'Bonnyrigg Heights Community Centre',
            'description': 'Meet the team, learn how CAWC programs operate, and explore practical ways to contribute to community activities.',
            'cta_text': 'View details',
            'cta_link': '/events/',
        }),
        ('event', {
            'date': '2026-07-09',
            'title': 'Women and Family Support Workshop',
            'location': 'Cabramatta, NSW',
            'description': 'A community education workshop focused on family wellbeing, safety information and referral pathways.',
            'cta_text': 'View details',
            'cta_link': '/events/',
        }),
    ],
    donation_section_title='Help keep community support accessible',
    donation_description='Your support helps CAWC continue culturally responsive programs, outreach, workshops and community activities for Cambodian families, seniors, women, children and newly arrived community members.',
    donation_cta_text='Donate Now',
    donation_cta_link='/#donate',
    donation_steps=[
        ('step', {
            'title': 'Support essential services',
            'description': 'Contribute to practical assistance, referrals and culturally safe guidance for families, seniors and newly arrived community members.',
        }),
        ('step', {
            'title': 'Sustain programs',
            'description': 'Help keep wellbeing activities, educational workshops and social connection programs accessible.',
        }),
        ('step', {
            'title': 'Strengthen connection',
            'description': 'Support community events, intergenerational activities and outreach that reduce isolation.',
        }),
        ('step', {
            'title': 'Build long-term capacity',
            'description': 'Strengthen the organisation so CAWC can keep responding to community needs over time.',
        }),
    ],
    volunteer_title='Volunteer with CAWC NSW',
    volunteer_description='Support community events, outreach, program activities and culturally responsive services by registering your interest with the CAWC team.',
    volunteer_cta_text='Express Interest',
    volunteer_cta_link='/get-involved/',
    faq_items=[
        ('faq', {
            'question': 'Who does CAWC support?',
            'answer': '<p>CAWC supports Cambodian families and community members in NSW, including seniors, women, children, newly arrived migrants and people seeking culturally responsive information or referrals.</p>',
        }),
        ('faq', {
            'question': 'How can I become a volunteer?',
            'answer': '<p>You can register your interest through the Get Involved page or speak with the team during community events and program sessions.</p>',
        }),
        ('faq', {
            'question': 'How do donations help?',
            'answer': '<p>Donations help sustain community programs, workshops, outreach, events and practical support. Specific donation details should be confirmed by CAWC before launch.</p>',
        }),
        ('faq', {
            'question': 'Where can I find upcoming activities?',
            'answer': '<p>Visit the Events page for upcoming sessions and community activities. Event details can be updated by CAWC staff in Wagtail.</p>',
        }),
    ],
    body=[
        ('heading', 'Welcome to the Cambodian-Australian Welfare Council of NSW'),
        ('image', None),   # replaced below after image is created
        ('button', {'text': 'View Programs', 'link': '/programs/'}),
    ],
)
root.add_child(instance=home)
print('[ok] Created: Home Page')

# Add image to home body
home_image = get_or_create_image('home-page-image', 'home-page-image.avif')
if home_image:
    home.hero_image = home_image
    home.body = [
        ('heading', 'Welcome to the Cambodian-Australian Welfare Council of NSW'),
        ('image', home_image),
        ('button', {'text': 'View Programs', 'link': '/programs/'}),
    ]
    home.save_revision().publish()

# Site config
Site.objects.create(
    hostname='localhost',
    port=8000,
    root_page=home,
    is_default_site=True,
    site_name='Cambodian Welfare Association',
)
print('[ok] Created: Site (localhost:8000)')

# About Index
about_index = AboutIndexPage(
    title='Who We Are',
    slug='about-us',
    body=[
        ('subheading', 'About CAWC'),
        ('heading', 'Who We Are'),
        ('paragraph', """
            <p>The Cambodian-Australian Welfare Council of NSW Inc. (CAWC) is a not-for-profit organisation. It was established in 1983 as Khmer Interagency (KI) by workers who worked with Khmer people, and it became incorporated in 1996.</p>
        """),
        ('paragraph', """
            <p>The name KI was later changed to CAWC. The organisation is a network of Khmer and non-Khmer workers interested in Khmer issues, and it meets on a regular basis to liaise, discuss, and plan programs and activities that respond to the needs of the Cambodian community.</p>
            <p>Today, CAWC NSW continues that role through advocacy, community programs, culturally responsive support, and opportunities that strengthen belonging, wellbeing, and participation across New South Wales.</p>
        """),
        ('button', {'text': 'Explore Our Programs', 'link': '/programs/'}),
        ('button', {'text': 'View Events', 'link': '/events/'}),
    ],
)
home.add_child(instance=about_index)
about_index.save_revision().publish()
print('[ok] Created: Who We Are')

if home_image:
    about_index.body.append(('image', home_image))
    about_index.save_revision().publish()

history_page = AboutSectionPage(
    title='History',
    slug='history',
    section_kind='history',
    body=[
        ('subheading', 'Our story'),
        ('heading', 'A History Built Through Community'),
        ('paragraph', """
            <p>The Cambodian-Australian Welfare Council of NSW (CAWC) was originally known as Khmer Interagency (KI). It was established in 1983 as an information-sharing forum and a means of support for those who work with Khmer clients or who are interested in Khmer issues.</p>
        """),
        ('paragraph', """
            <p>The group met monthly to liaise, share information, discuss problems, and lobby for better services for Khmer settlers. KI became registered as a charitable organisation and adopted a more formal structure through the election of a committee.</p>
            <p>Members elected the following committee roles: Chairperson, Vice-Chairperson, Treasurer, Secretary, and three Committee Members. Over time, that structure helped the organisation grow into the CAWC NSW community presence that exists today.</p>
        """),
        ('button', {'text': 'Support Our Work', 'link': '/#donate'}),
        ('button', {'text': 'Meet Our Staff', 'link': '/about-us/staff/'}),
    ],
    stats=[
        ('stat', {
            'value': '1983',
            'label': 'Year founded',
            'description': 'CAWC NSW began as Khmer Interagency to meet urgent community settlement and support needs.',
        }),
        ('stat', {
            'value': '40+',
            'label': 'Years of community service',
            'description': 'A long-standing presence supporting Cambodian families and wider multicultural communities in NSW.',
        }),
    ],
    timeline_items=[
        ('milestone', {
            'year': '1983',
            'title': 'Khmer Interagency established',
            'description': 'Community workers formed Khmer Interagency as a forum for information-sharing, support, and advocacy.',
        }),
        ('milestone', {
            'year': '1996',
            'title': 'CAWC NSW incorporated',
            'description': 'The organisation adopted a more formal structure and strengthened its capacity to respond to community priorities.',
        }),
        ('milestone', {
            'year': 'Today',
            'title': 'Expanding community-led services',
            'description': 'CAWC NSW continues to deliver programs, community events, outreach, and culturally responsive support across New South Wales.',
        }),
    ],
)
about_index.add_child(instance=history_page)
history_page.save_revision().publish()
print('[ok] Created: About section - History')

if home_image:
    history_page.body.append(('image', home_image))
    history_page.body.append(('carousel', [home_image]))
    history_page.save_revision().publish()

vision_page = AboutSectionPage(
    title='Vision',
    slug='vision',
    section_kind='vision',
    body=[
        ('subheading', 'Long-term aspiration'),
        ('heading', 'Our Vision'),
        ('paragraph', """
            <p>People from the Cambodian community living in NSW are part of and welcomed to a harmonious, diverse Australian society.</p>
        """),
        ('paragraph', """
            <p>This vision guides CAWC NSW's long-term commitment to connection, inclusion, cultural continuity, and active participation in the wider community.</p>
        """),
        ('button', {'text': 'Read Our Mission', 'link': '/about-us/mission/'}),
        ('button', {'text': 'Explore Programs', 'link': '/programs/'}),
    ],
)
about_index.add_child(instance=vision_page)
vision_page.save_revision().publish()
print('[ok] Created: About section - Vision')

if home_image:
    vision_page.body.append(('image', home_image))
    vision_page.save_revision().publish()

mission_page = AboutSectionPage(
    title='Mission',
    slug='mission',
    section_kind='mission',
    body=[
        ('subheading', 'Why we exist'),
        ('heading', 'Our Mission'),
        ('paragraph', """
            <p>We provide excellent and inclusive services to enable individuals and families to fully participate in the Australian way of life.</p>
        """),
        ('paragraph', """
            <p>In practice, this means creating trusted pathways to support, social connection, cultural belonging, advocacy, and practical information for Cambodian community members across New South Wales.</p>
        """),
        ('button', {'text': 'Support CAWC NSW', 'link': '/#donate'}),
        ('button', {'text': 'See Community Events', 'link': '/events/'}),
    ],
    feature_items=[
        ('item', {
            'title': 'Connect people to support',
            'description': 'We create trusted pathways to information, referrals, and culturally responsive support for Cambodian families and individuals.',
            'icon': '01',
        }),
        ('item', {
            'title': 'Strengthen community wellbeing',
            'description': 'Our programs and gatherings reduce isolation, strengthen resilience, and create spaces for mutual care and participation.',
            'icon': '02',
        }),
        ('item', {
            'title': 'Preserve language and culture',
            'description': 'We help community members maintain Cambodian cultural identity and share it confidently across generations.',
            'icon': '03',
        }),
        ('item', {
            'title': 'Build participation and belonging',
            'description': 'We encourage people to feel connected to each other and take part in the broader New South Wales community.',
            'icon': '04',
        }),
    ],
)
about_index.add_child(instance=mission_page)
mission_page.save_revision().publish()
print('[ok] Created: About section - Mission')

objectives_page = AboutSectionPage(
    title='Objectives',
    slug='objectives',
    section_kind='objectives',
    body=[
        ('subheading', 'What guides our work'),
        ('heading', 'Our Objectives'),
        ('paragraph', """
            <p>CAWC NSW's formal objectives guide its commitment to community benefit, service access, harmony, advocacy, connection and the preservation of Cambodian culture.</p>
        """),
        ('button', {'text': 'Meet Our Board', 'link': '/about-us/board/'}),
        ('button', {'text': 'Explore Programs', 'link': '/programs/'}),
    ],
    feature_items=[
        ('item', {
            'eyebrow': 'Community benefit',
            'title': 'Promote the wellbeing of Khmer residents in NSW',
            'description': 'Promote the benefit of Khmer residents in NSW without discrimination by race, religion, political belief, social status, or gender.',
        }),
        ('item', {
            'eyebrow': 'Quality of life',
            'title': 'Provide services and supports that improve daily life',
            'description': 'Provide services and supports to improve the quality of life of people from the Cambodian community living in NSW.',
        }),
        ('item', {
            'eyebrow': 'Connection',
            'title': 'Create opportunities to connect with wider communities',
            'description': 'Create opportunities for people from the Cambodian community living in NSW to connect with and better understand people from other communities living in NSW.',
        }),
        ('item', {
            'eyebrow': 'Harmony',
            'title': 'Promote respect for similarities and differences',
            'description': 'Promote harmony and respect for our similarities and differences within our own community and the wider Australian community.',
        }),
        ('item', {
            'eyebrow': 'Advocacy',
            'title': 'Share knowledge and represent community interests',
            'description': 'Be a point of connection for workers from the Cambodian community and those working with people from the Cambodian community to share experiences, information, and ideas on issues affecting the community, and represent the interests and views of members.',
        }),
        ('item', {
            'eyebrow': 'Culture',
            'title': 'Preserve and promote Cambodian culture',
            'description': 'Support language, heritage, and intergenerational cultural continuity through community-led activity.',
        }),
    ],
)
about_index.add_child(instance=objectives_page)
objectives_page.save_revision().publish()
print('[ok] Created: About section - Objectives')

board_page = BoardPage(
    title='Board',
    slug='board',
    intro="""
        <p>Our board helps guide CAWC NSW with stewardship, governance, and a strong commitment to the Cambodian community in New South Wales.</p>
    """,
    story_heading='Leading with Accountability and Care',
    story_text="""
        <p>The CAWC NSW board supports the organisation's governance, accountability and long-term direction. Board members help protect the organisation's community-led purpose while guiding decisions that affect programs, partnerships and service delivery.</p>
        <p>Photos and short biographies can be added in Wagtail as they are confirmed by the client.</p>
    """,
    primary_cta_text='Support CAWC',
    primary_cta_link='/#donate',
    secondary_cta_text='Meet Our Staff',
    secondary_cta_link='/about-us/staff/',
    directors=[
        ('director', {
            'image': None,
            'name': 'Sarithya Tuy',
            'role': 'Chair Person',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Rattana Pin',
            'role': 'Vice-Chair Person',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Nola Randall, OAM JP',
            'role': 'Director of HR',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Lachlan Erskine',
            'role': 'Director of Finance',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Dara Sok',
            'role': 'Director of IT',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Sorathy Michell',
            'role': 'General Board Member',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Lisa Nagatsuka',
            'role': 'General Board Member',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Sophina Neang',
            'role': 'General Board Member',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Panhary Soeu',
            'role': 'General Board Member',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Kim Chansreysor',
            'role': 'Assistant Treasurer',
            'bio': '',
        }),
        ('director', {
            'image': None,
            'name': 'Ry',
            'role': 'Director of Evaluation and Impact Measurement',
            'bio': '',
        }),
    ],
)
about_index.add_child(instance=board_page)
board_page.save_revision().publish()
print('[ok] Created: Board')

if home_image:
    board_page.featured_image = home_image
    board_page.save_revision().publish()

staff_page = StaffPage(
    title='Staff',
    slug='staff',
    intro="""
        <p>CAWC NSW staff deliver day-to-day programs, coordination, settlement support, community care and culturally responsive outreach across New South Wales.</p>
    """,
    primary_cta_text='Explore Programs',
    primary_cta_link='/programs/',
    secondary_cta_text='See Community Events',
    secondary_cta_link='/events/',
    staff_members=[
        ('staff_member', {
            'image': None,
            'name': 'Thin Em, JP',
            'role': 'Project Officer & Office Coordinator',
            'team': 'Operations & Leadership',
            'description': 'Coordinates office operations and supports the smooth delivery of CAWC NSW projects and community activities.',
            'working_hours': 'Working hours: Wed, Thu & Fri 9 to 5',
            'focus': '',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Ny Seng',
            'role': 'Projects Worker',
            'team': 'Operations & Leadership',
            'description': 'Supports program delivery and community engagement across CAWC NSW activities.',
            'working_hours': 'Hours: Mon & Wed 9 to 5',
            'focus': '',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Rachana Bunn',
            'role': 'Project Officer',
            'team': 'Operations & Leadership',
            'description': 'Helps coordinate projects and community-facing initiatives across the organisation.',
            'working_hours': '',
            'focus': '',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Chhun Y Ich',
            'role': '(SETS) Worker',
            'team': 'Settlement Support',
            'description': 'Supports community members through settlement information, referrals, and practical guidance.',
            'working_hours': 'Working on: Wed & Thu',
            'focus': 'Settlement Engagement and Transition Support',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Y Hourng Kov',
            'role': 'Day Care Worker',
            'team': 'Community Care Programs',
            'description': 'Helps deliver day care support and creates welcoming spaces for community participation.',
            'working_hours': '',
            'focus': 'Elderly Day Care',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Sok Chhin Chhai',
            'role': 'Elderly Day Care',
            'team': 'Community Care Programs',
            'description': 'Supports elderly day care activities and contributes to safe, engaging weekly sessions.',
            'working_hours': 'Working on: Wed, Thu & Friday',
            'focus': 'Elderly Day Care',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Sok Im Chhai',
            'role': 'Elderly Day Care',
            'team': 'Community Care Programs',
            'description': 'Supports community care activities and assists with culturally responsive service delivery.',
            'working_hours': 'Working on: Monday',
            'focus': 'Elderly Day Care',
        }),
        ('staff_member', {
            'image': None,
            'name': 'Omethip Phommachanh',
            'role': 'Multicultural Access Referral Services for the Lao community',
            'team': 'Multicultural Outreach',
            'description': 'Supports multicultural access and referrals for Lao community members through community-based assistance.',
            'working_hours': 'Working on: Monday & Thursday',
            'focus': 'Multicultural Access Referral Services',
        }),
    ],
)
about_index.add_child(instance=staff_page)
staff_page.save_revision().publish()
print('[ok] Created: Staff')

if home_image:
    staff_page.featured_image = home_image
    staff_page.save_revision().publish()

# Programs Index
programs_index = ProgramsIndexPage(
    title='Programs',
    slug='programs',
    intro='<p>CAWC NSW delivers culturally responsive programs supporting Cambodian seniors, women, children, newly arrived migrants, older Laotian adults and families across New South Wales. Programs are designed to reduce isolation, improve wellbeing, strengthen cultural connection, and connect community members with services and support.</p>',
)
home.add_child(instance=programs_index)
programs_index.save_revision().publish()
print('[ok] Created: Programs Index')

events_page = EventsPage(
    title='Events',
    slug='events',
    intro='Explore CAWC NSW community events, information sessions, cultural activities and program updates. Confirmed dates and registration details can be added in Wagtail as activities are announced.',
    featured_label='Featured Partnership',
    featured_title='The NSW Settlement Partnership',
    featured_summary='The NSW Settlement Partnership is a consortium of 21 settlement organisations across the state, led by SSI, working together to support refugee and migrant communities through the Settlement Engagement and Transition Support (SETS) program funded by the Department of Home Affairs.',
    featured_date_text='',
    featured_time_text='',
    featured_venue_text='',
    featured_entry_text='',
    featured_details=[
        ('detail', 'CAWC NSW is one of 21 consortium partners working across New South Wales.'),
        ('detail', 'The partnership has supported 185,886 clients through 546,628 instances of service across 88 local government areas since 2015.'),
        ('detail', 'It helps refugee and migrant communities connect with practical settlement support and community services.'),
    ],
    featured_cta_text='Visit The NSW Settlement Partnership',
    featured_cta_link='https://nsp.ssi.org.au/',
)
home.add_child(instance=events_page)
events_page.save_revision().publish()
print('[ok] Created: Events')

# ── Program pages ─────────────────────────────────────────────────────────────

carousel_image = get_or_create_image('home-page-image', 'home-page-image.avif')

if carousel_image:
    events_page.featured_image = carousel_image
    events_page.featured_map_image = carousel_image

events_page.save_revision().publish()

# 1. Cambodian Seniors Hub
seniors_hub = ProgramPage(
    title='Cambodian Seniors Hub',
    slug='cambodian-seniors-hub',
    category='seniors',
    summary='A weekly gathering for Cambodian-Australian seniors that tackles social isolation, builds community connections, and improves access to aged care and health services.',
    cost='Free',
    language='Khmer and English',
    schedule='Every Thursday, 10am – 12pm',
    venue='Bonnyrigg Heights Community Centre',
    cta_heading='Support our seniors program',
    outcomes='<ul><li>Reduces social isolation for 30+ Cambodian seniors each week</li><li>Improves access to My Aged Care and health services</li><li>Partially funded by Fairfield City Council 2024–2025</li><li>Sessions delivered in the Khmer language</li></ul>',
    audience='<p>Cambodian-Australian seniors residing in Fairfield and Liverpool City. The program is free and open to all. Sessions are facilitated in the Khmer language.</p>',
    gallery_note='See more photos related to the Cambodian Seniors Hub in our gallery.',
    program_tag='cambodian-seniors-hub',
    body=[
        ('heading', 'Cambodian Seniors Hub: Fostering Community Connection'),
        ('subheading', 'Proudly sponsored by Fairfield City Council 2024–2025'),
        ('paragraph', '<p>The Cambodian Seniors Hub is an ongoing initiative established by CAWC several years ago. It offers a safe space for seniors to meet weekly and directly addresses ongoing challenges related to isolation caused by a lack of regular social connections, which negatively affect their mental and physical health.</p><p>The program aims to increase awareness of social services by fostering social inclusion, addressing physical and mental health concerns, and improving access to essential services such as My Aged Care, local service providers, and information on elder abuse.</p><p>Each session features morning tea, gentle physical exercises, an information session on healthcare and senior support services, memory-stimulating games, and a shared potluck lunch.</p><p>CAWC takes pride in covering the costs of this project and greatly appreciates the dedication of our volunteers and staff. In 2024–2025 we are grateful to Fairfield City Council for their generous partial funding of $3,000, which significantly supports our initiative.</p>'),
    ],
)
if carousel_image:
    seniors_hub.body.append(('photo_grid', [{'image': carousel_image, 'caption': 'Morning tea session, Bonnyrigg Heights Community Centre'}]))

programs_index.add_child(instance=seniors_hub)
seniors_hub.save_revision().publish()
print('[ok] Created: Cambodian Seniors Hub')

# 2. Cyber Security for Vulnerable People
cyber_security = ProgramPage(
    title='Cyber Security for Vulnerable People',
    slug='cyber-security',
    category='digital',
    summary='Practical cyber safety education that helps vulnerable community members recognise online risks, avoid scams and build confidence using digital services.',
    cost='Free',
    language='English',
    cta_heading='Help protect your community',
    audience='<p>Vulnerable Australians, including seniors and community members with limited digital literacy, who may be at risk of online scams, fraud, or cyber harm.</p>',
    gallery_note='See more photos related to this cyber security project in our gallery.',
    program_tag='cyber-security',
    body=[
        ('heading', 'Cyber Security for Vulnerable People'),
        ('paragraph', '<p>This project uplifts cyber security literacy for vulnerable Australians and expands on the national cyber security awareness campaign.</p><p>CAWC delivers practical, accessible cyber safety education to community members who may be at risk of online scams, fraud, or other cyber threats. Sessions are designed to be approachable and relevant to everyday digital life, helping participants stay safe online with confidence.</p>'),
    ],
)
programs_index.add_child(instance=cyber_security)
cyber_security.save_revision().publish()
print('[ok] Created: Cyber Security for Vulnerable People')

# 3. Settlement Engagement and Transition Support (SETS)
sets_program = ProgramPage(
    title='Settlement Engagement and Transition Support (SETS)',
    slug='settlement-engagement-and-transition-support-program-sets',
    category='settlement',
    summary='Supporting eligible humanitarian visa holders and newly arrived migrants from Cambodia in their integration into Australian society, with a focus on women\'s inclusion and prevention of family violence.',
    cost='Free',
    language='Khmer and English',
    cta_heading='Support new arrivals in our community',
    audience='<p>Eligible humanitarian visa holders and newly arrived migrants from Cambodia. The program has a particular focus on women\'s social and economic inclusion.</p>',
    gallery_note='See more photos related to SETS activities in our gallery.',
    program_tag='sets',
    body=[
        ('heading', 'Settlement Engagement and Transition Support Program'),
        ('paragraph', '<p>The SETS program aims to support eligible clients, humanitarian visa holders, and newly arrived migrants from Cambodia in their integration into Australian society.</p><p>The program focuses on women\'s social and economic inclusion, the primary prevention of domestic and family violence, and alignment with the Refugee and Humanitarian Entrant Settlement and Integration Outcomes Framework.</p><p>Through practical support, referrals, and community connection, CAWC helps newly arrived community members build the skills and networks they need to live independently and participate fully in Australian life.</p>'),
    ],
)
programs_index.add_child(instance=sets_program)
sets_program.save_revision().publish()
print('[ok] Created: SETS Program')

# 4. Khmer Elderly Day Care Project
khmer_daycare = ProgramPage(
    title='Khmer Elderly Day Care Project',
    slug='khmer-elderly-day-care',
    category='seniors',
    summary='A long-running program providing Cambodian seniors with opportunities to socialise, learn, and access health and welfare information in a supportive, Khmer-language environment.',
    cost='Free',
    language='Khmer',
    schedule='Mondays 10am–1pm and Wednesdays 10am–1pm',
    venue='CabraVale Club Resort',
    cta_heading='Support the Khmer Elderly Day Care Project',
    outcomes='<ul><li>Grown from 10 to 90+ participants since 2006</li><li>Two weekly groups running across Mondays and Wednesdays</li><li>Delivered entirely in the Khmer language</li><li>Improves health literacy and reduces loneliness in seniors 65+</li></ul>',
    audience='<p>Cambodian seniors aged 65 and over. The program has grown from 10 participants at its founding in 2006 to over 90 elderly participants each week across two groups.</p>',
    gallery_note='See more photos related to the Khmer Elderly Day Care Project in our gallery.',
    program_tag='khmer-elderly-day-care',
    body=[
        ('heading', 'Khmer Elderly Day Care Project'),
        ('subheading', 'Running since 2006, now supporting 90+ seniors each week'),
        ('highlight_box', {'stat': '90+', 'label': 'participants each week', 'description': 'Grown from just 10 participants when the project launched in 2006.'}),
        ('paragraph', '<p>The Khmer Elderly Day Care Project started in 2006, growing from a single group of 10 elderly participants aged over 65 to two groups with a total of over 90 elderly participants each week.</p><p>The first group meets weekly on Mondays (10am–1pm) and the second meets weekly on Wednesdays (10am–1pm) at CabraVale Club Resort.</p><p>The aim of the program is to provide opportunities for Cambodian seniors to socialise, converse in Khmer, make new friends, learn about services that can benefit them, and increase their awareness and knowledge of health issues that affect older people.</p>'),
    ],
)
programs_index.add_child(instance=khmer_daycare)
khmer_daycare.save_revision().publish()
print('[ok] Created: Khmer Elderly Day Care Project')

# 5. Empowering Older Laotian Adults
laotian_adults = ProgramPage(
    title='Empowering Older Laotian Adults through Social Support Initiatives',
    slug='empowering-older-laotian-adults-through-social-support-initiatives',
    category='social',
    summary='Free social support for older Laotian community members in the Fairfield LGA, cultivating meaningful connections and empowering independent living through community engagement.',
    cost='Free',
    language='Lao and English',
    cta_heading='Support older Laotian community members',
    audience='<p>Older individuals in the Laotian community residing within the Fairfield Local Government Area. The program is free of charge.</p>',
    gallery_note='See more photos related to this Laotian social support project in our gallery.',
    program_tag='laotian-social-support',
    body=[
        ('heading', 'Empowering Older Laotian Adults through Social Support Initiatives'),
        ('paragraph', '<p>This project aims to provide free social support to older individuals in the Laotian community residing within the Fairfield LGA. Its primary objective is to cultivate meaningful connections among participants and empower them to live independently in their homes.</p><p>By addressing crucial challenges such as social isolation and loneliness, the initiative strives to improve the quality of life for older adults while promoting their active engagement in community activities.</p>'),
    ],
)
programs_index.add_child(instance=laotian_adults)
laotian_adults.save_revision().publish()
print('[ok] Created: Empowering Older Laotian Adults')

# 6. Cambodian Women Support Hub
women_hub = ProgramPage(
    title='Cambodian Women Support Hub',
    slug='cambodian-women-support-hub',
    category='women',
    summary='Educational and recreational activities supporting disadvantaged Cambodian women, grandparents, and single mothers caring for school-aged children.',
    cost='Free',
    language='Khmer and English',
    cta_heading='Support Cambodian women in our community',
    audience='<p>Disadvantaged Cambodian women, grandparents, and single mothers caring for school-aged children.</p>',
    gallery_note='See more photos related to the Cambodian Women Support Hub in our gallery.',
    program_tag='women-support-hub',
    body=[
        ('heading', 'Cambodian Women Support Hub'),
        ('paragraph', '<p>The Cambodian Women Support Hub offers educational and recreational activities to support disadvantaged Cambodian women, grandparents, and single mothers caring for school-aged children.</p><p>The hub provides a welcoming and culturally responsive environment where participants can build skills, access information, and connect with others in the community. Activities are designed to promote wellbeing, confidence, and independence.</p>'),
    ],
)
programs_index.add_child(instance=women_hub)
women_hub.save_revision().publish()
print('[ok] Created: Cambodian Women Support Hub')

# 7. Cambodian Children Support Project
children_project = ProgramPage(
    title='Cambodian Children Support Project',
    slug='cambodian-children-support-project',
    category='children',
    summary='Free homework help, tutoring, and school holiday activities for Cambodian children aged 8–12 years in Fairfield LGA, delivered every Saturday during school term via Zoom.',
    cost='Free',
    language='English',
    schedule='Every Saturday during school term, 10am – 2pm (via Zoom)',
    cta_heading='Support Cambodian children in our community',
    outcomes='<ul><li>Running for 8+ years through NSW ClubGrants</li><li>Improves literacy and numeracy for Year 3–6 students</li><li>Supports school-to-high-school transition</li><li>Free of charge — fully funded for eligible families</li></ul>',
    audience='<p>Cambodian children aged 8–12 years (Year 3 to Year 6) living in the Fairfield LGA. The program is free and funded through NSW ClubGrants.</p>',
    gallery_note='See more photos related to the Cambodian Children Support Project in our gallery.',
    program_tag='children-support-project',
    body=[
        ('heading', 'Cambodian Children Support Project'),
        ('subheading', 'Running for over 8 years through NSW ClubGrants'),
        ('paragraph', '<p>The Cambodian Children Support Project provides free homework help, tutoring, and school holiday activities for Cambodian children aged 8–12 years living in Fairfield LGA. The project has been running for over 8 years through NSW ClubGrants.</p><p>The program aims to increase self-confidence and self-esteem, ease the transition from primary school to high school, and improve literacy and numeracy skills.</p><p>Sessions run every Saturday during school term from 10am to 2pm for Year 3 to Year 6 students via the Zoom platform.</p>'),
    ],
)
programs_index.add_child(instance=children_project)
children_project.save_revision().publish()
print('[ok] Created: Cambodian Children Support Project')

# Get Involved Page
get_involved = GetInvolvedPage(
    title='Get Involved',
    slug='get-involved',
    intro='<p>There are many ways to contribute to CAWC NSW — whether you volunteer your time, join as an intern, or express your interest in a specific role. Every contribution helps strengthen our community.</p>',

    volunteer_heading='Volunteer',
    volunteer_intro='<p>Volunteers are the backbone of CAWC NSW. Whether you can offer a few hours a week or contribute specialist skills, your time makes a real difference to Cambodian families across New South Wales.</p>',
    volunteer_roles=[
        ('role', {
            'title': 'Community Support Volunteer',
            'description': 'Assist with day-to-day community activities, provide friendly company at seniors programs, and help facilitate group sessions.',
            'commitment': 'Flexible hours',
            'icon': '01',
        }),
        ('role', {
            'title': 'Events & Outreach Volunteer',
            'description': 'Help plan and run community events, cultural celebrations, and outreach activities that bring people together.',
            'commitment': 'Event-based',
            'icon': '02',
        }),
        ('role', {
            'title': 'Administration Volunteer',
            'description': 'Support the CAWC NSW office with data entry, correspondence, and general administrative tasks.',
            'commitment': 'A few hours/week',
            'icon': '03',
        }),
    ],

    internship_heading='Internship',
    internship_intro='<p>CAWC NSW offers internship placements for students and recent graduates looking to gain hands-on experience in community services, social work, administration and communications.</p>',
    internship_roles=[
        ('role', {
            'title': 'Community Services Intern',
            'description': 'Work alongside staff to support program delivery, client engagement, and service coordination across our community programs.',
            'commitment': '2–3 days/week',
            'icon': '01',
        }),
        ('role', {
            'title': 'Communications & Media Intern',
            'description': 'Assist with social media, newsletters, content creation, and promoting CAWC NSW programs and events.',
            'commitment': 'Flexible',
            'icon': '02',
        }),
    ],

    eoi_heading='Express Your Interest',
    eoi_intro='<p>Ready to get involved? Fill in your details below and a member of the CAWC NSW team will be in touch to discuss the best opportunity for you.</p>',
)
home.add_child(instance=get_involved)
get_involved.save_revision().publish()
print('[ok] Created: Get Involved Page')

if home_image:
    get_involved.featured_image = home_image
    get_involved.save_revision().publish()

# ── Donate Page ──────────────────────────────────────────────────────────────

donate_page = DonatePage(
    title='Donate',
    slug='donate',
    hero_eyebrow='Support CAWC NSW',
    hero_title='Your contribution strengthens Cambodian families across NSW.',
    hero_intro=(
        '<p>Donations fund advocacy, culturally responsive programs, and practical '
        'support for seniors, women, children and newly arrived community members. '
        'Every contribution — large or small — helps the work continue.</p>'
    ),
    why_title='Where your donation goes',
    why_intro=(
        '<p>CAWC NSW operates with care and accountability. The majority of every '
        'dollar funds direct community work and culturally responsive support.</p>'
    ),
    impact_cards=[
        ('card', {
            'title': 'Community Programs',
            'description': "Cambodian Seniors Hub, Women's Support, Children's programs and more — delivered in language and in culture.",
            'amount_example': '$50 funds program materials for one session.',
        }),
        ('card', {
            'title': 'Advocacy & Outreach',
            'description': 'Helping community members access government services, navigate settlement, and connect with culturally informed support.',
            'amount_example': '$100 supports a week of outreach contact.',
        }),
        ('card', {
            'title': 'Cultural Connection',
            'description': 'Cultural events, language preservation, and intergenerational programs that keep heritage alive in NSW.',
            'amount_example': '$250 contributes to cultural event delivery.',
        }),
    ],
    how_title='How your donation makes a difference',
    how_intro=(
        '<p>From the moment you donate, your contribution moves directly into '
        'community-facing work.</p>'
    ),
    how_steps=[
        ('step', {'title': 'Direct community programs',
                  'description': 'Funds go straight into running services for Cambodian families across NSW.'}),
        ('step', {'title': 'Operational essentials',
                  'description': 'Keeps program staff, venues and culturally informed delivery sustainable.'}),
        ('step', {'title': 'Outreach & advocacy',
                  'description': 'Supports community members to access services and navigate settlement.'}),
        ('step', {'title': 'Long-term resilience',
                  'description': 'Builds CAWC capacity to continue serving the community for decades.'}),
    ],
    trust_title='A registered, accountable charity',
    trust_text=(
        '<p>CAWC NSW is a registered not-for-profit organisation with a community-elected '
        'board. We publish annual reports outlining how funds are used and the outcomes '
        'achieved across our programs.</p>'
    ),
    abn_number='Available on request',
    faq_title='Common questions about donating',
    faq_items=[
        ('faq', {'question': 'Are donations tax-deductible?',
                 'answer': '<p>CAWC NSW is a registered not-for-profit. Please check with our team for current tax-deductible status and to receive a receipt for your contribution.</p>'}),
        ('faq', {'question': 'Can I donate monthly?',
                 'answer': '<p>Yes — choose the Monthly option in the donation form to set up a recurring contribution. You can adjust or cancel at any time.</p>'}),
        ('faq', {'question': 'Where can I see how funds are used?',
                 'answer': '<p>Our annual reports detail program outcomes and financial summaries. Visit the Resources page to download them.</p>'}),
        ('faq', {'question': 'How do I make a major gift or corporate donation?',
                 'answer': '<p>Get in touch with the team directly using the contact details below — we would love to talk about partnership and major gift opportunities.</p>'}),
    ],
    major_gifts_title='Considering a major gift?',
    major_gifts_text=(
        '<p>For major gifts, corporate sponsorship, in-kind support, or partnership '
        'enquiries, please reach out to the CAWC NSW team directly.</p>'
    ),
    major_gifts_email='cawcnsw@cambodianwelfare.org.au',
    major_gifts_phone='+61 2 9876 5432',
)
home.add_child(instance=donate_page)
donate_page.save_revision().publish()
print('[ok] Created: Donate Page')

# ── Resources Page ───────────────────────────────────────────────────────────

resources_page = ResourcesPage(
    title='Resources',
    slug='resources',
    intro=(
        'Access our archive of annual reports, community guides and organisational documents. '
        'We maintain these records to ensure transparency and provide cultural context for our work.'
    ),
)
home.add_child(instance=resources_page)
resources_page.save_revision().publish()
print('[ok] Created: Resources Page')

# Annual Reports (newest first — featured card uses first entry)
annual_reports_data = [
    (2025, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_7d2cae57d3f246b891834940649ceb1c.pdf'),
    (2024, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_dc4f7c91e7fe4ba3a3c6d91d1fe627b9.pdf'),
    (2023, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_3e2658d5c3af4fc7bc262361127a4cc1.pdf'),
    (2022, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_ab40fc73de854318a5fd301650299de6.pdf'),
    (2021, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_1cd4c7e8ffe14835a65232aea1ecb73f.pdf'),
    (2020, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_e8bf0de5ef9a49b1801412d3caa553c8.pdf'),
    (2019, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_e9135d75cd5242f6a8ea639941d33d67.pdf'),
    (2018, ''),  # no document available
    (2017, 'http://www.cambodianwelfare.org.au/files/agm2017.pdf'),
    (2016, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_a9df1a60879643239d1bc0e60c7c6e72.pdf'),
    (2015, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_86ad347ef1d346b89ac96e785bd25c67.pdf'),
    (2014, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_fcc96b02d61e4139a068ba727ce42b5a.pdf'),
    (2013, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_c295c0b5076144159759156c327952b4.pdf'),
    (2012, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_e4600c97d0aa4e958cc730d3c3d7a8cc.pdf'),
    (2011, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_b1155412a4314c1b9fdab97999330aa8.pdf'),
    (2010, 'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_b05009f9dd3644b78445833d11c114fe.pdf'),
    (2009, 'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_e6897379ee674368964b69dae3438905.pdf'),
]
for i, (year, url) in enumerate(annual_reports_data):
    AnnualReport.objects.create(page=resources_page, year=year, url=url, sort_order=i)
print(f'[ok] Created: {len(annual_reports_data)} Annual Reports')

# Community Publications
publications_data = [
    ('Digital Security',       'Cybersecurity Community Forum',                        'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_44bcdf6745a8437087695e930b00e8aa.pdf'),
    ('Institutional Advocacy', 'State Conference 2003',                                'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_8f2d9d76009d45aaa0637f4b35fd867b.pdf'),
    ('Health & Culture',       'Khmer Culture and Attitude Towards Health 2010',       'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_86d50b6409964fa79827828ff71fe867.pdf'),
    ('Archive Conference',     'State Conference 1998',                                'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_77e071e2f4964de4a12b3917973beea2.pdf'),
    ('Cultural History',       'Cambodian Culture & Customs Seminar',                  'https://www.cambodianwelfare.org.au/_files/ugd/77d59b_7c478cb30bf746cdba958c25e8a5b153.pdf'),
    ('Social History',         'Settlement of People from Cambodia',                   'https://www.cambodianwelfare.org.au/_files/ugd/7351f5_adda05a424074f99897e2220450e2bc8.pdf'),
    ('Current Services',       'SETS Brochure',                                        ''),  # no document available
]
for i, (category, title, url) in enumerate(publications_data):
    CommunityPublication.objects.create(page=resources_page, category=category, title=title, url=url, sort_order=i)
print(f'[ok] Created: {len(publications_data)} Community Publications')

print()
print('[ok] Seed complete.')
print('   Log in at http://localhost:8000/admin/ to review the content.')

