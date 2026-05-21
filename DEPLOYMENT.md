# Deployment — Railway

This project is deployed on [Railway](https://railway.app) using Docker.

---

## Prerequisites

- A [Railway](https://railway.app) account
- The [Railway CLI](https://docs.railway.app/develop/cli) installed (`npm install -g @railway/cli`)
- Your code pushed to a GitHub repository

---

## Production stack

| Layer           | Technology                                       |
|-----------------|--------------------------------------------------|
| Hosting         | Railway                                          |
| Container       | Docker                                           |
| Web server      | Gunicorn                                         |
| Database        | PostgreSQL (Railway managed — via `DATABASE_URL`)|
| Static files    | WhiteNoise (`CompressedStaticFilesStorage`)      |
| Backend         | Django 6 + Wagtail CMS                           |
| Styling         | Tailwind CSS v4                                  |
| Package manager | uv                                               |

---

## How the Dockerfile works

**Build time** (runs once per deploy, baked into the image):
1. Installs Python dependencies via `uv sync --frozen --no-dev`
2. Runs `collectstatic` to gather and compress static files

**Runtime** (runs every time the container starts):
1. `python manage.py migrate` — applies any pending database migrations
2. `gunicorn a_core.wsgi` — starts the web server

> `DATABASE_URL` is only needed at runtime (for migrate + gunicorn), not at build time. `collectstatic` does not require a database connection.

---

## Steps

### 1. Create a new Railway project

Log in and link your GitHub repo:

```bash
railway login
railway init
```

Or go to [railway.app/new](https://railway.app/new) and connect your GitHub repo directly.

---

### 2. Add a PostgreSQL database

In the Railway dashboard:

1. Click **+ New** → **Database** → **PostgreSQL**
2. Railway automatically injects `DATABASE_URL` into your service as an environment variable — no manual config needed.

---

### 3. Set environment variables

In your Railway service under **Variables**, add:

| Variable               | Value                                            |
|------------------------|--------------------------------------------------|
| `DJANGO_SECRET_KEY`    | A long random string (generate one below)        |
| `ALLOWED_HOSTS`        | `your-app.up.railway.app` (your Railway domain)  |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.up.railway.app`                |
| `DEBUG`                | `False`                                          |
| `MEDIA_URL`            | `/media/`                                        |
| `MEDIA_ROOT`           | `/app/media`                                     |

`DATABASE_URL` is injected automatically by the PostgreSQL service — do not add it manually.

To generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

### 4. Add persistent media storage

Wagtail image uploads are split across two places:

- The PostgreSQL database stores image metadata, page content, captions, and chooser references.
- The filesystem stores the actual uploaded image files under `MEDIA_ROOT`.

On Railway, the container filesystem is not permanent unless a volume is mounted. For production media:

1. Open the Railway web service, not the Postgres service.
2. Add a persistent Railway volume.
3. Mount it at `/app/media`.
4. Set `MEDIA_ROOT=/app/media`.
5. Set `MEDIA_URL=/media/`.

With this setup, files uploaded through Wagtail admin are stored in the Railway volume and survive deploys. Wagtail originals usually live under `/app/media/original_images/`, while generated renditions live under `/app/media/images/`.

Do not commit production uploads to Git. The repo's local `media/` folder is for development assets and local imports only.

---

### 5. Compile and commit the CSS

The Docker build runs inside Railway's infrastructure and does not have the Tailwind binary. The compiled CSS must be committed to the repo before deploying.

```bash
# Compile locally (macOS/Linux)
./static/css/tailwindcss -i static/css/input.css -o static/css/output.css

# Compile locally (Windows)
.\static\css\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css

# Commit
git add static/css/output.css
git commit -m "compile css"
git push
```

> Re-run this and push whenever you change `input.css` or add new Tailwind classes to templates.

---

### 6. Deploy

Push to your connected GitHub branch — Railway deploys automatically on every push. To trigger a deploy manually:

```bash
railway up
```

---

### 7. Create a superuser

```bash
railway run python manage.py createsuperuser
```

---

### 8. Configure the Wagtail site

1. Log in to the Wagtail admin at `https://your-app.up.railway.app/admin/`
2. Go to **Settings** → **Sites**
3. Update the default site hostname to your Railway domain

---

## Railway CLI reference

These commands require the CLI to be installed (`npm install -g @railway/cli`) and your project linked.

### Link your local repo to the Railway project

Run this once in the project directory:

```bash
railway login
railway link
```

`railway link` prompts you to select your team, project, and environment. After linking, all `railway` commands in this directory target that project automatically.

---

### SSH into the running container

```bash
railway ssh
```

Opens a shell directly inside the running container with all environment variables injected. Useful for one-off commands, debugging, or inspecting the filesystem.

---

### Run a management command against production

```bash
railway run python manage.py <command>
```

Runs the command locally but with all Railway environment variables (including `DATABASE_URL`) injected. The code runs on your machine, not inside the container.

Examples:

```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py update_index
railway run python manage.py shell
```

---

### Tail live logs

```bash
railway logs
```

---

## Known gotchas

**`collectstatic` crashes with `MissingFileError`**
WhiteNoise's manifest storage parses CSS files for URL references and chokes on Tailwind's `@import "tailwindcss"` directive in `input.css`, treating the Tailwind binary as a missing static file. The project uses `CompressedStaticFilesStorage` instead, which compresses assets without URL rewriting.

**`InvalidStorageError: Could not find config for 'default'`**
Overriding Django's `STORAGES` setting requires both the `default` (media files) and `staticfiles` keys to be present. Defining only `staticfiles` removes the `default` backend, which Wagtail's image models depend on at startup.

**`DATABASE_URL` not set during build**
`collectstatic` does not need the database and runs fine without `DATABASE_URL`. The warning logged during the build step is harmless.

**`DATABASE_URL` set but app still can't see it**
Railway creates `DATABASE_URL` on the PostgreSQL service, not the web service. The two services are separate — variables do not share automatically. Fix: open your **web service** → **Variables** tab and add `DATABASE_URL` there directly, or use Railway's reference syntax to keep it in sync:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
```

Replace `Postgres` with whatever your database service is named in the Railway dashboard.
