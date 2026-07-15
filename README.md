# Ontime Cue Sheet

A small web app that reads the current rundown from an Ontime stage and renders a printable PDF cue sheet with WeasyPrint.

After connecting, the app uses the Ontime rundown title, lists every discovered custom field, and lets the user choose which columns appear in the PDF. Cue text uses the event colour, with the same colour applied to the row background at 15% opacity. Long rundowns can be paged through in the browser preview and flow across PDF pages with column headers repeated on each page.

## Status

This is an early MVP. It uses Ontime's documented read-only `GET /data/rundowns/current` endpoint. For a password-protected Cloud stage, generate an authenticated Companion share link in Ontime and paste that complete URL into the app. Its `token` query parameter is preserved when the rundown endpoint is requested; credentials are never embedded in the PDF.

## Run locally

WeasyPrint requires native libraries. On macOS, install WeasyPrint's system dependencies first, then:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Or run the container:

```sh
docker build -t ontime-cue-sheet .
docker run --rm -p 8000:8000 --env-file .env ontime-cue-sheet
```

## Configuration

Copy `.env.example` to `.env` for local configuration.

- `ONTIME_BASE_URL`: default stage URL shown in the form
- `ONTIME_AUTH_HEADER`: optional header name, such as `Authorization`
- `ONTIME_AUTH_VALUE`: optional complete header value, such as `Bearer …`

Do not commit `.env` or credentials.

### Password-protected Ontime Cloud stages

In Ontime, open `Editor` → `Settings` → `Sharing and reporting` → `Share link`. Select `Companion`, enable `Authenticate`, create the share link, and paste the complete generated URL into this app.

## What to validate next

1. Capture a real current-rundown response as a sanitized fixture and lock down the response model.

## References

- [Ontime documentation](https://docs.getontime.no/ontime/)
- [Ontime HTTP API](https://docs.getontime.no/api/protocols/http/)
- [Ontime event data](https://docs.getontime.no/api/data/event-data/)
- [Ontime Cloud login](https://docs.getontime.no/ontime-cloud/tips/login-with-auth/)
