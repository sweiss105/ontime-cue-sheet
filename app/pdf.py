from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

TEMPLATES = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))


def clock(value: Any) -> str:
    try:
        total_seconds = int(value) // 1000
    except (TypeError, ValueError):
        return ""
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


env.filters["clock"] = clock


def render_pdf(
    events: list[dict[str, Any]],
    title: str,
    paper_size: str = "Letter",
    orientation: str = "landscape",
) -> bytes:
    html = env.get_template("cue_sheet.html").render(
        events=events,
        title=title.strip() or "Cue Sheet",
        generated_at=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    )
    page_css = f"@page {{ size: {paper_size} {orientation}; }}"
    return HTML(string=html, base_url=str(TEMPLATES)).write_pdf(
        stylesheets=[CSS(string=page_css)]
    )
