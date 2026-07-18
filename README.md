# Ontime Cue Sheet

A Netlify-hosted web app that reads the current rundown from an Ontime stage and renders a printable PDF cue sheet with PDFMake.

After importing cues, the app uses the Ontime project title for the cue-sheet header, lists every discovered custom field, and lets the user choose and drag the optional PDF fields into their desired column order. Cue notes can be included directly beneath each title in smaller italic text. If project metadata is unavailable, the current rundown title is used as a fallback. Cue, Start, Duration, and Title remain fixed on the left; Cue, Start, and Duration stay compact while the remaining columns size themselves from their content. Cue text is black, with the event colour applied to the row background at 15% opacity and a 5% white overlay on alternating rows for easier scanning. PDFs use quarter-inch page margins. The browser preview measures the selected columns and wrapped row content so each sheet fills before the next page begins; long PDFs repeat the column headers on every page. Every generated sheet carries a local-time version code in the lower-right footer and uses the same value in filenames such as `Project Name-CUESHEET-20260715-1310.pdf`.

## Status

This is an early MVP. It uses Ontime's documented read-only `GET /data/rundowns/current` endpoint. The public importer accepts HTTPS stage and Companion share URLs from `cloud.getontime.no`. For a password-protected Cloud stage, generate an authenticated Companion share link in Ontime and paste that complete URL into the app. Its `token` query parameter is preserved when the rundown endpoint is requested; credentials are never embedded in the PDF or included in upstream error messages.

## Run locally

Install Node.js 22 or newer and the Netlify CLI, then:

```sh
npm install
npm run dev
```

The Netlify CLI prints the local URL, normally `http://localhost:8888`.

Run the automated build and PDF smoke test with:

```sh
npm run build
```

## Deploy to Netlify

The repository is configured for Netlify continuous deployment in `netlify.toml`. The interface is served from `public/`; cue import and PDF generation run in Netlify Functions.

```sh
netlify login
netlify link
netlify deploy
```

Use the generated deploy URL to verify the homepage, `/health`, live cue import, and PDF generation before assigning a custom domain. Production releases should be made through the connected Git repository or with `netlify deploy --prod` after a successful draft deploy. Do not store an authenticated Ontime Companion URL in Netlify environment variables.

## Configuration

Copy `.env.example` to `.env` only if the Ontime stage requires a server-side authorization header.

- `ONTIME_AUTH_HEADER`: optional header name, such as `Authorization`
- `ONTIME_AUTH_VALUE`: optional complete header value, such as `Bearer …`

Do not commit `.env` or credentials.

### Password-protected Ontime Cloud stages

In Ontime, open `Editor` → `Settings` → `Sharing and reporting` → `Share link`. Select `Companion`, enable `Authenticate`, create the share link, and paste the complete generated URL into this app.

## What to validate next

1. Capture a real current-rundown response as a sanitized fixture and lock down the response model.

## License

Ontime Cue Sheet is licensed under the [Zero-Clause BSD license](LICENSE), identified by the SPDX expression `0BSD`. Anyone may use, copy, modify, or distribute the software for any purpose, with or without a fee and without an attribution requirement.

Attribution to [Steve Weiss](AUTHORS.md) is appreciated but not required. The software is provided "AS IS," without warranty, and the author disclaims liability as stated in the license.

PDFMake and the project's other dependencies remain under their respective licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution and licensing details.

## AI-assisted development disclaimer

This project was developed with assistance from generative AI, including OpenAI Codex. No independent human source-code review or security audit has been performed. Automated tests and functional checks do not replace human review; users should review and test the software before relying on it. See [DISCLAIMER.md](DISCLAIMER.md) for the complete notice.

## References

- [Ontime documentation](https://docs.getontime.no/ontime/)
- [Ontime HTTP API](https://docs.getontime.no/api/protocols/http/)
- [Ontime event data](https://docs.getontime.no/api/data/event-data/)
- [Ontime Cloud login](https://docs.getontime.no/ontime-cloud/tips/login-with-auth/)
