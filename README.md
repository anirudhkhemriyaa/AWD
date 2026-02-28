## AWD – Data & Email Automation Platform

AWD is a Django-based SaaS-style platform that helps organizations **import, manage, and export structured data** (such as employees and students) and **send tracked bulk emails** to their audiences.  
It combines CSV-based data automation, subscription-aware usage limits, and email campaign tracking into a single, Dockerized stack that is easy to deploy.

### Why this is useful

- **Centralized data operations**: Import and export business data (employees, students, etc.) through a web UI instead of brittle one-off scripts.
- **Background processing at scale**: Heavy CSV imports/exports and email sends run asynchronously via Celery and Redis, keeping the UI responsive.
- **Subscription & usage limits**: Per-user subscription plans with per‑day limits for imports, exports, and emails to control cost and abuse.
- **Bulk emailing with tracking**: Create email lists, send campaigns, and measure open/click rates for each campaign.
- **Production-ready stack**: Gunicorn, Nginx, PostgreSQL, Redis, and Django are wired together using Docker Compose for reproducible deployments.

---

## Features

- **User & company management**
  - Custom user model with company details (sector, company size, contact info).
  - Profile page with recent activity and subscription status.

- **Data import & export**
  - Upload CSV files for domain models (e.g. `Student`, `Employee` and others).
  - Server-side validation of CSVs before processing.
  - Asynchronous import/export jobs via Celery workers.
  - History log for each job (success / failed / processing).

- **Subscription & daily limits**
  - `SubscriptionPlan` model to define pricing, duration, and per‑day limits.
  - Per-user `UserSubscription` with validity checks.
  - `DailyUsage` tracking for imports, exports, and emails.

- **Email campaigns**
  - Email lists (`List`) and subscribers (`Subscriber`).
  - Rich HTML email editing using CKEditor.
  - Bulk emails sent asynchronously via Celery.
  - Open and click tracking (`EmailTracking`) with dashboards.
  - Email delivery via Sendinblue (Anymail backend).

- **AI-assisted content (optional)**
  - Integration with Google Gemini API to assist with email content (configured via `GEMINI_API_KEY`).

- **Modern stack & tooling**
  - Django with a custom user model.
  - PostgreSQL as the main database.
  - Redis as Celery broker.
  - Gunicorn as the WSGI server.
  - Nginx as reverse proxy.
  - Static files served via WhiteNoise.
  - Fully Dockerized with `docker-compose.yml`.

---

## Architecture Overview

The project is structured as a classic Django monolith with supporting services:

- **Web (`web`)**
  - Django application (`awd_main`) served by Gunicorn on port `8000`.
  - Handles all HTTP requests, authentication, dashboards, and management UI.
  - Serves static files via WhiteNoise and media files from `/app/media`.

- **Celery worker (`celery`)**
  - Processes background jobs for:
    - CSV imports and exports.
    - Bulk email sending.
    - Email tracking related tasks.
  - Uses Redis as the broker (`REDIS_URL`).

- **PostgreSQL (`db`)**
  - Main relational database for Django.
  - Data persisted in a Docker volume `postgres_data`.

- **Redis (`redis`)**
  - Message broker for Celery.

- **Nginx (`nginx`)**
  - Reverse proxy listening on host port `80`.
  - Forwards traffic to the `web` service on port `8000`.

All services and their relationships are defined in `docker-compose.yml`.

---

## Prerequisites

- **Docker** (20.x or later recommended)
- **Docker Compose**  
  - Either the `docker compose` CLI (Docker v2+)  
  - Or legacy `docker-compose` (v1.x)

You do **not** need to install Python or PostgreSQL locally if you using Docker.

---

## Configuration (.env)

The project expects a `.env` file at the project root. This file is:

- Loaded by Django settings via `python-decouple`.
- Loaded by Docker Compose for the `db`, `web`, and `celery` services.

Below is an example `.env` you can adapt:

```env
# --- Django ---
SECRET_KEY=change-me-to-a-strong-secret-key
DEBUG=True

# External URL used in links / tracking
BASE_URL=http://localhost
CSRF_TRUSTED_ORIGINS=http://localhost

# --- PostgreSQL (used by db container and Django) ---
POSTGRES_DB=awd
POSTGRES_USER=awd
POSTGRES_PASSWORD=awdpassword
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- Redis / Celery ---
REDIS_URL=redis://redis:6379/0

# --- Email (Sendinblue via Anymail) ---
SENDINBLUE_API_KEY=your-sendinblue-api-key

# --- Optional: Google Gemini API for AI features ---
GEMINI_API_KEY=your-gemini-api-key
```

> **Note**: Use strong, unique values for `SECRET_KEY` and `POSTGRES_PASSWORD` in any non-local environment.

---

## Running the project with Docker

### 1. Clone the repository

```bash
git clone <https://github.com/anirudhkhemriyaa/AWD.git> AWD
cd AWD
```

### 2. Create the `.env` file

Create a `.env` file at the project root using the example above and adjust values as needed.

### 3. Build the images

```bash
docker compose build
```

This will:

- Build the Django/Gunicorn image using the `Dockerfile`.
- Install dependencies from `requirements.txt`.
- Collect static files via `python manage.py collectstatic --noinput`.

### 4. Run database migrations

Run migrations inside the `web` container:

```bash
docker compose run --rm web python manage.py migrate
```



Follow the prompts to set up an admin account.

### 6. Start the full stack

```bash
docker compose up -d
```

This starts:

- `redis` – Redis broker
- `db` – PostgreSQL database
- `web` – Django + Gunicorn
- `celery` – Celery worker
- `nginx` – Reverse proxy on port `80`

### 7. Access the application

- **Main site**: `http://localhost`

Log in using the superuser credentials you created earlier.

To view logs for a specific service:

```bash
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f db
```

To stop the stack:

```bash
docker compose down
```

> **Note**: Data is persisted in Docker volumes (`postgres_data`, `media_data`) even after `docker compose down`. Use `docker compose down -v` to remove volumes as well.

---

## Development tips

- **Run management commands**

  You can run any Django management command in the `web` container:

  ```bash
  docker compose run --rm web python manage.py <command>
  ```

  Examples:

  ```bash
  docker compose run --rm web python manage.py shell
  docker compose run --rm web python manage.py makemigrations
  ```

- **Static & media files**
  - Static files are collected into `/app/staticfiles` during the image build.
  - User uploads (email attachments, etc.) are stored in `/app/media`, backed by the `media_data` Docker volume.

---

## Project structure (high level)

Some key directories and modules:

- `awd_main/`
  - Core Django project, settings, URLs, WSGI config.
- `Data_entry/`
  - Models for `CustomUser`, `Student`, `Employee`, subscription plans, usage tracking, CSV import/export logic, and related views.
- `Email/`
  - Email lists, subscribers, email campaigns, tracking models, and views.
- `uploads/`
  - File upload model used for CSV imports.
- `nginx/default.conf`
  - Nginx configuration used by the `nginx` service in Docker.
- `docker-compose.yml`
  - Definition of all services (web, celery, db, redis, nginx, volumes, and networks).
- `Dockerfile`
  - Build instructions for the Django/Gunicorn container.

---



With these steps and configurations, you can run AWD as a **production-like, containerized data & email automation platform** with minimal manual setup.

