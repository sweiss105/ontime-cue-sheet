# Ontime Cue Sheet

A small web app that reads the current rundown from an Ontime stage and renders a printable PDF cue sheet with WeasyPrint.

After importing cues, the app uses the Ontime project title for the cue-sheet header, lists every discovered custom field, and lets the user choose and drag the optional PDF fields into their desired column order. Cue notes can be included directly beneath each title in smaller italic text. If project metadata is unavailable, the current rundown title is used as a fallback. Cue, Start, Duration, and Title remain fixed on the left; Cue, Start, and Duration stay compact while the remaining columns size themselves from their content. Cue text is black, with the event colour applied to the row background at 15% opacity and a 5% white overlay on alternating rows for easier scanning. PDFs use quarter-inch page margins. The browser preview measures the selected columns and wrapped row content so each sheet fills before the next page begins; long PDFs repeat the column headers on every page.

## Status

This is an early MVP. It uses Ontime's documented read-only `GET /data/rundowns/current` endpoint. The public importer accepts HTTPS stage and Companion share URLs from `cloud.getontime.no`. For a password-protected Cloud stage, generate an authenticated Companion share link in Ontime and paste that complete URL into the app. Its `token` query parameter is preserved when the rundown endpoint is requested; credentials are never embedded in the PDF or included in upstream error messages.

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

## Deploy to Vercel

The Vercel deployment uses `Dockerfile.vercel` so WeasyPrint's native Pango and font dependencies are installed in the runtime image. The server reads Vercel's `PORT` environment variable automatically.

```sh
vercel login
vercel link
vercel deploy
```

Use the generated Vercel URL to verify the homepage, `/health`, live cue import, and PDF generation before assigning a custom domain. Do not store an authenticated Ontime Companion URL in Vercel environment variables.

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
