from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .ontime import OntimeError, RundownData, fetch_current_rundown
from .pdf import render_pdf

ROOT = Path(__file__).parent
templates = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
app = FastAPI(title="Ontime Cue Sheet")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> str:
    return templates.get_template("index.html").render(
        base_url=os.getenv("ONTIME_BASE_URL", ""), error=None
    )


async def _get_rundown(base_url: str) -> RundownData:
    return await fetch_current_rundown(
        base_url,
        os.getenv("ONTIME_AUTH_HEADER"),
        os.getenv("ONTIME_AUTH_VALUE"),
    )


@app.post("/connection-test")
async def connection_test(base_url: str = Form(...)) -> JSONResponse:
    try:
        rundown = await _get_rundown(base_url)
        return JSONResponse({"ok": True, "event_count": len(rundown["events"])})
    except OntimeError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


@app.post("/preview")
async def preview(
    base_url: str = Form(...),
    include_skipped: bool = Form(False),
) -> JSONResponse:
    try:
        rundown = await _get_rundown(base_url)
        events = rundown["events"]
        if not include_skipped:
            events = [event for event in events if not event.get("skip")]
        return JSONResponse(
            {
                "ok": True,
                "title": rundown["title"],
                "custom_fields": rundown["custom_fields"],
                "events": events,
            }
        )
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
    include_notes: bool = Form(False),
    selected_custom_fields: list[str] | None = Form(None),
    fields_configured: bool = Form(False),
    selected_fields: list[str] | None = Form(None),
) -> Response:
    try:
        rundown = await _get_rundown(base_url)
        events = rundown["events"]
        if not include_skipped:
            events = [event for event in events if not event.get("skip")]
        safe_paper = paper_size if paper_size in {"Letter", "A4"} else "Letter"
        safe_orientation = orientation if orientation in {"portrait", "landscape"} else "landscape"
        allowed_fields = set(rundown["custom_fields"])
        if fields_configured:
            requested_fields = selected_fields or []
            include_notes = include_notes or "Notes" in requested_fields
            safe_fields = list(
                dict.fromkeys(
                    field
                    for field in requested_fields
                    if field != "Notes" and field in allowed_fields
                )
            )
        else:
            safe_custom_fields = [
                field for field in (selected_custom_fields or []) if field in allowed_fields
            ]
            safe_fields = safe_custom_fields
        pdf = render_pdf(
            events,
            title,
            safe_paper,
            safe_orientation,
            include_notes=include_notes,
            selected_fields=safe_fields,
        )
    except OntimeError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)
    filename = "cue-sheet.pdf"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
