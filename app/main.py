from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
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


@app.post("/generate")
async def generate(
    request: Request,
    base_url: str = Form(...),
    title: str = Form("Cue Sheet"),
) -> Response:
    try:
        events = await fetch_current_rundown(
            base_url,
            os.getenv("ONTIME_AUTH_HEADER"),
            os.getenv("ONTIME_AUTH_VALUE"),
        )
        pdf = render_pdf(events, title)
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

