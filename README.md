# Pastebin-Lite

A lightweight Pastebin-like web application that allows users to create text pastes and share them via a unique URL. Pastes can optionally expire based on time-to-live (TTL) or view count limits.

## Features

* Create and share text pastes
* Optional paste expiry (TTL)
* Optional maximum view count
* Safe HTML rendering
* API and UI support
* Deterministic expiry testing for automated graders

## Tech Stack

* Backend: Django + Django REST Framework
* Database: PostgreSQL (production) / SQLite (local only)
* Deployment: Vercel / Render

## Running Locally

```bash
git clone <your-repo-url>
cd pastebinLite
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit:

* UI: [https://pastebinlite-7x18.onrender.com/]
* Health: [https://pastebinlite-7x18.onrender.com/api/healthz](https://pastebinlite-7x18.onrender.com/api/healthz)

## API Endpoints

### Health Check

```
GET /api/healthz
```

### Create Paste

```
POST /api/pastes
```

```json
{
  "content": "Hello world",
  "ttl_seconds": 60,
  "max_views": 5
}
```

### Fetch Paste (API)

```
GET /api/pastes/{id}
```

### View Paste (HTML)

```
GET /p/{id}
```

## Deterministic Testing

If `TEST_MODE=1` is set:

* Header `x-test-now-ms` is used as current time for expiry logic

## Persistence Layer

* Production uses PostgreSQL to ensure data persistence across serverless requests
* SQLite is used only for local development

## Design Decisions

* Atomic view decrement to prevent over-serving
* Explicit 404 for expired or exhausted pastes
* Safe content rendering to prevent XSS
* Stateless server design for serverless compatibility
