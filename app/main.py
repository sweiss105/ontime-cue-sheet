from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .ontime import OntimeError, fetch_current_rundown
from .pdf import render_pdf

ROOT = Path(__file__).parent
templates = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
app = FastAPI(title="Ontime Cue Sheet")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> str:
    return templates.get_template("index.html").render(
        base_url=os.getenv("ONTIME_BASE_URL", ""), error=None
    )


async def _get_events(base_url: str) -> list[dict]:
    return await fetch_current_rundown(
        base_url,
        os.getenv("ONTIME_AUTH_HEADER"),
        os.getenv("ONTIME_AUTH_VALUE"),
    )


@app.post("/connection-test")
async def connection_test(base_url: str = Form(...)) -> JSONResponse:
    try:
        events = await _get_events(base_url)
        return JSONResponse({"ok": True, "event_count": len(events)})
    except OntimeError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


@app.post("/preview")
async def preview(
    base_url: str = Form(...),
    include_skipped: bool = Form(False),
) -> JSONResponse:
    try:
        events = await _get_events(base_url)
        if not include_skipped:
            events = [event for event in events if not event.get("skip")]
        return JSONResponse({"ok": True, "events": events})
    except OntimeError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


@app.post("/generate")
async def generate(
    request: Request,
    base_url: str = Form(...),
    title: str = Form("Cue Sheet"),
    paper_size: str = Form("Letter"),
    orientation: str = Form("landscape"),
    include_skipped: bool = Form(False),
) -> Response:
    try:
        events = await _get_events(base_url)
        if not include_skipped:
            events = [event for event in events if not event.get("skip")]
        safe_paper = paper_size if paper_size in {"Letter", "A4"} else "Letter"
        safe_orientation = orientation if orientation in {"portrait", "landscape"} else "landscape"
        pdf = render_pdf(events, title, safe_paper, safe_orientation)
    except OntimeError as exc:
        html = templates.get_template("index.html").render(base_url=base_url, error=str(exc))
        return HTMLResponse(html, status_code=502)
    filename = "cue-sheet.pdf"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
