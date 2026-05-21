# CAWC NSW - Website Redesign

> Portfolio note: this repository is a sanitized public copy of a client/student project codebase.
> Private planning files, local environment files, database files, agent/Claude instructions,
> and Git history from the working client repository have been removed. Demo media is included
> so the site can be reviewed locally with realistic visuals.

CAWC Website Redesign is a Django + Wagtail CMS project for the Cambodian Australian Welfare Council of NSW (CAWC NSW). It is the student redesign codebase for a modern, CMS-managed nonprofit website focused on trust, clarity, donations, volunteers, community programs, and events.

The current repository runs locally with SQLite, Wagtail, and Tailwind CSS. The approved deployment direction is Railway hosting, PostgreSQL, Stripe for donations, and external media storage.

## Tech Stack

- Backend: Django 6
- CMS: Wagtail 7.3
- Styling: Tailwind CSS v4 via standalone binary
- UI helpers: daisyUI plugin files in `static/css`
- Python package manager: `uv`
- Local database: SQLite
- Planned production database: PostgreSQL
- Planned hosting: Railway
- Planned payments: Stripe

## Current Repo Status

What is implemented today:
- Home page
- About section
- Programs section
- Events landing page
- Shared navbar and footer
- Wagtail-managed page content
- Seed script for demo content

What is planned but not fully wired in code yet:
- PostgreSQL environment-based database config
- Stripe integration
- Production email integration
- Full sitemap from the planning docs
- Railway-ready production settings

## Prerequisites

Install these before running the project:
- Python 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Windows PowerShell

This repo does **not** currently use Node or `package.json`. Tailwind is run through the checked-in standalone executable at `static/css/tailwindcss.exe`.

## Clone And Install

```powershell
git clone <your-repo-url>
cd cambodian-welfare
uv sync
```

## Environment Setup

Create your local env file from the example:

```powershell
Copy-Item .env.example .env
```

Then update `.env` with your local values.

### Minimum local variable

The current codebase only requires this variable to run safely:

- `DJANGO_SECRET_KEY`

### Additional planned variables

The `.env.example` also includes placeholders for Railway, PostgreSQL, Stripe, email, and Wagtail deployment settings. Those are included so the repo documents the agreed project direction, even though not all of them are wired into settings yet.

## Local Setup Commands

### 1. Apply migrations

```powershell
uv run python manage.py migrate
```

### 2. Create a superuser

```powershell
uv run python manage.py createsuperuser
```

### 3. Optional: seed demo content

If you want the local site to include the demo page tree and sample Wagtail content, run:

```powershell
Get-Content .\seed.py | uv run python manage.py shell
```

Important:
- The seed script is destructive.
- It deletes existing non-root pages, Wagtail sites, and Wagtail images before recreating demo content.
- Only run it on a local development database you are happy to reset.

### 4. Run Tailwind in watch mode

Keep this running in a separate PowerShell window while you work on templates:

```powershell
.\static\css\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css --watch
```

If you only need a one-off CSS build:

```powershell
.\static\css\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css
```

### 5. Run the Django development server

```powershell
uv run python manage.py runserver
```

Open:
- Site: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Wagtail admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- Search page: [http://127.0.0.1:8000/search/](http://127.0.0.1:8000/search/)

## Migration Commands

Create new migrations:

```powershell
uv run python manage.py makemigrations
```

Create migrations for a specific app:

```powershell
uv run python manage.py makemigrations a_home
uv run python manage.py makemigrations a_about
uv run python manage.py makemigrations a_events
```

Apply migrations:

```powershell
uv run python manage.py migrate
```

Check project health:

```powershell
uv run python manage.py check
```

## Wagtail Admin Notes

- Log in at `/admin/` with the superuser you created locally.
- The navbar now depends on the live Wagtail page tree, so pages must exist in the CMS for navigation links to appear.
- If you want the same demo structure the team has been using, run the seed script after migrations.
- There is no committed default admin account.

## Seed Content And Images

The seed script expects optional local assets in `media/seed_images/`.

Currently referenced:
- `media/seed_images/home-page-image.avif`

If the file is missing, the seed script will still run, but seeded hero/gallery areas may fall back to text-only content.

## Important Folders

```text
a_core/                 Django project settings, URLs, shared views
a_home/                 Home page model and migrations
a_about/                About-related page models, template tags, migrations
a_programs/             Programs index and program detail pages
a_events/               Events landing page model
a_contact/              Placeholder app for future contact implementation
a_resources/            Placeholder app for future resources implementation
templates/              Global and page templates
templates/includes/     Shared navbar, footer, streamfield include
static/css/             Tailwind input/output files and standalone binary
static/img/             Static image assets such as logo
media/                  Local uploaded files and optional seed images
docs/                   Local planning docs used for product/design direction
seed.py                 Destructive local content bootstrap script
```

## Template And Static Structure

Current page templates live under:
- `templates/a_home/`
- `templates/a_about/`
- `templates/a_programs/`
- `templates/a_events/`

Shared layout lives in:
- `templates/base.html`
- `templates/includes/navbar_main.html`
- `templates/includes/footer_main.html`
- `templates/includes/_streamfield.html`

Static assets live in:
- `static/css/`
- `static/img/`

## Tailwind Setup

Tailwind is already configured in `static/css/input.css`.

Key details:
- It uses the standalone binary `tailwindcss.exe`
- It scans templates in `templates/` and the app template directories listed in `input.css`
- There is no Node build pipeline in the current repo

If a new template path is added later, update the `@source` entries in `static/css/input.css`.

## Common Setup Issues

### PowerShell does not support `< seed.py`

Use this instead:

```powershell
Get-Content .\seed.py | uv run python manage.py shell
```

### Styles are not updating

- Make sure the Tailwind watcher is running
- Hard refresh the browser after restarting the watcher
- Confirm your template path is included in `static/css/input.css`

### `OperationalError` or missing columns after pulling changes

Run:

```powershell
uv run python manage.py migrate
```

If the local DB is disposable and badly out of sync, remove `db.sqlite3`, migrate again, and optionally reseed.

### Navbar links are missing

The current navbar uses live Wagtail pages. If the expected pages do not exist in the database, those links will not appear. Run the seed script or create the pages manually in Wagtail admin.

### Seeded content looks incomplete

Some seeded sections expect local images in `media/seed_images/`. Missing images do not stop the seed, but they do reduce visual completeness.

### Search field appears but returns little or no content

Search depends on indexed Wagtail page content. Seed or create content first.

## Team Onboarding Caveats

- `docs/` is intentionally treated as local planning material, not teammate runtime dependency.
- The repo currently runs locally with SQLite, not PostgreSQL.
- Railway, PostgreSQL, Stripe, and production email are agreed project decisions, but they are not fully implemented in settings yet.
- The seed script is useful for syncing demo content across teammates, but it should not be used casually because it resets Wagtail content.
- `media/` is local-only. Uploaded images from one machine do not automatically appear on another machine unless shared separately or recreated through seed assets.

## Railway Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full step-by-step Railway deployment instructions.

High-level deployment direction for this project:
- Host the Django app on Railway
- Use Railway PostgreSQL in production
- Store media in external object storage
- Configure Stripe keys and webhook secret via environment variables
- Set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `WAGTAILADMIN_BASE_URL` for the production domain
- Run `collectstatic` and migrations during deployment

## Stripe Environment Variables

These are included in `.env.example` for the approved architecture:
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`

They are documented now so the integration path is clear, even though Stripe checkout/webhook code has not yet been added to this repo.

## Recommended Local Run Checklist

```powershell
uv sync
Copy-Item .env.example .env
uv run python manage.py migrate
uv run python manage.py createsuperuser
Get-Content .\seed.py | uv run python manage.py shell
.\static\css\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css --watch
uv run python manage.py runserver
```
