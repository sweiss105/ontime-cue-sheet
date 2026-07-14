# Ontime Cue Sheet

A small web app that reads the current rundown from an Ontime stage and renders a printable PDF cue sheet with WeasyPrint.

## Status

This is an early MVP. It uses Ontime's documented read-only `GET /data/rundowns/current` endpoint. Ontime Cloud login uses TOTP, but the public documentation does not currently specify a machine-to-machine Cloud API authentication flow. The client therefore supports an optional authorization header supplied through environment variables; credentials are never entered into or embedded in the PDF.

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

## What to validate next

1. Confirm the exact hosted stage URL and whether `/data/rundowns/current` is accessible to a logged-out read-only client.
2. If Cloud protects the endpoint, confirm the supported service authentication mechanism with Ontime.
3. Capture a real current-rundown response as a sanitized fixture and lock down the response model.
4. Decide which standard and custom fields belong on the production cue sheet.

## References

- [Ontime documentation](https://docs.getontime.no/ontime/)
- [Ontime HTTP API](https://docs.getontime.no/api/protocols/http/)
- [Ontime event data](https://docs.getontime.no/api/data/event-data/)
- [Ontime Cloud login](https://docs.getontime.no/ontime-cloud/tips/login-with-auth/)

