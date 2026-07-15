# Copyright 2026 Steve Weiss
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
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

HEX_COLOUR = re.compile(r"^#([0-9a-fA-F]{6})$")
VERSION_CODE = re.compile(r"^\d{8}-\d{4}$")


def normalize_version_code(value: Any = None) -> str:
    candidate = str(value or "").strip()
    if VERSION_CODE.fullmatch(candidate):
        try:
            datetime.strptime(candidate, "%Y%m%d-%H%M")
        except ValueError:
            pass
        else:
            return candidate
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M")


def cue_colour(value: Any) -> str:
    match = HEX_COLOUR.fullmatch(str(value or "").strip())
    return f"#{match.group(1).upper()}" if match else ""


def cue_tint(value: Any) -> str:
    colour = cue_colour(value)
    if not colour:
        return ""
    red, green, blue = (int(colour[index:index + 2], 16) for index in (1, 3, 5))
    return f"rgba({red}, {green}, {blue}, 0.15)"


env.filters["cue_colour"] = cue_colour
env.filters["cue_tint"] = cue_tint


def render_pdf(
    events: list[dict[str, Any]],
    title: str,
    paper_size: str = "Letter",
    orientation: str = "landscape",
    include_notes: bool = True,
    selected_custom_fields: list[str] | None = None,
    selected_fields: list[str] | None = None,
    version_code: str | None = None,
) -> bytes:
    if selected_custom_fields is None:
        selected_custom_fields = list(
            dict.fromkeys(
                field
                for event in events
                if isinstance(event.get("custom"), dict)
                for field in event["custom"]
            )
        )
    if selected_fields is None:
        selected_fields = selected_custom_fields
    include_notes = include_notes or "Notes" in selected_fields
    selected_fields = list(dict.fromkeys(field for field in selected_fields if field != "Notes"))
    safe_version_code = normalize_version_code(version_code)
    html = env.get_template("cue_sheet.html").render(
        events=events,
        title=title.strip() or "Cue Sheet",
        generated_at=datetime.strptime(safe_version_code, "%Y%m%d-%H%M").strftime("%Y-%m-%d %H:%M"),
        version_code=safe_version_code,
        include_notes=include_notes,
        selected_fields=selected_fields,
    )
    page_css = f"@page {{ size: {paper_size} {orientation}; }}"
    return HTML(string=html, base_url=str(TEMPLATES)).write_pdf(
        stylesheets=[CSS(string=page_css)]
    )
