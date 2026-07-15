from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.main import app, pdf_filename
from app.ontime import (
    OntimeError,
    build_project_url,
    build_rundown_url,
    extract_events,
    extract_rundown,
    validate_ontime_url,
)
from app.pdf import clock, cue_colour, cue_tint, env, normalize_version_code, render_pdf


EVENT = {
    "type": "event",
    "id": "evt-1",
    "cue": "A1",
    "title": "Doors",
    "note": "House opens",
    "timeStart": 36_000_000,
    "duration": 1_800_000,
    "colour": "#339E4E",
    "custom": {"Audio": "Walk-in playlist", "Video": "Holding slide"},
}


def test_extract_events_from_payload():
    assert extract_events({"payload": {"events": [EVENT]}}) == [EVENT]


def test_extract_events_from_normalized_rundown():
    group = {"type": "group", "id": "group-1", "title": "Act One"}
    rundown = {
        "id": "rundown-1",
        "title": "Daily Show",
        "flatOrder": ["group-1", "evt-1"],
        "entries": {"evt-1": EVENT, "group-1": group},
    }
    assert extract_events(rundown) == [EVENT]


def test_extract_rundown_metadata_and_custom_fields():
    rundown = extract_rundown(
        {
            "title": "Fall Kick Off 2026",
            "flatOrder": ["evt-1"],
            "entries": {"evt-1": EVENT},
        },
        {"title": "WCTC Underestimated to Unstoppable"},
    )
    assert rundown["title"] == "WCTC Underestimated to Unstoppable"
    assert rundown["rundown_title"] == "Fall Kick Off 2026"
    assert rundown["custom_fields"] == ["Audio", "Video"]


def test_rundown_title_is_used_when_project_title_is_unavailable():
    rundown = extract_rundown(
        {
            "title": "Fall Kick Off 2026",
            "flatOrder": ["evt-1"],
            "entries": {"evt-1": EVENT},
        }
    )

    assert rundown["title"] == "Fall Kick Off 2026"


def test_empty_normalized_rundown_is_valid():
    assert extract_events({"flatOrder": [], "entries": {}}) == []


def test_authenticated_share_link_preserves_token():
    assert build_rundown_url("https://stage.example.com?token=secret") == (
        "https://stage.example.com/data/rundowns/current/?token=secret"
    )


def test_cloud_prefix_is_preserved():
    assert build_rundown_url("https://cloud.example.com/my-stage/?token=secret") == (
        "https://cloud.example.com/my-stage/data/rundowns/current/?token=secret"
    )


def test_project_url_preserves_cloud_prefix_and_token():
    assert build_project_url("https://cloud.example.com/my-stage/?token=secret") == (
        "https://cloud.example.com/my-stage/data/project/?token=secret"
    )


def test_public_importer_accepts_ontime_cloud_share_urls():
    validate_ontime_url("https://cloud.getontime.no/my-stage?token=secret")


def test_public_importer_rejects_non_ontime_and_unsafe_urls():
    unsafe_urls = [
        "http://cloud.getontime.no/my-stage",
        "https://cloud.getontime.no.evil.example/my-stage",
        "https://user:password@cloud.getontime.no/my-stage",
        "https://cloud.getontime.no:8443/my-stage",
        "https://cloud.getontime.no/my-stage#fragment",
        "https://cloud.getontime.no/",
    ]

    for unsafe_url in unsafe_urls:
        try:
            validate_ontime_url(unsafe_url)
        except OntimeError:
            continue
        raise AssertionError(f"Expected URL to be rejected: {unsafe_url}")


def test_clock_formats_milliseconds():
    assert clock(36_061_000) == "10:01:01"


def test_pdf_filename_uses_document_title_and_cuesheet_suffix():
    version = "20260715-1310"
    assert pdf_filename("WCTC Underestimated to Unstoppable", version) == (
        "WCTC Underestimated to Unstoppable-CUESHEET-20260715-1310.pdf"
    )
    assert pdf_filename("  Show / Finale: 2026.pdf  ", version) == (
        "Show - Finale- 2026-CUESHEET-20260715-1310.pdf"
    )
    assert pdf_filename("Show-CUESHEET", version) == "Show-CUESHEET-20260715-1310.pdf"


def test_version_code_accepts_expected_format_and_replaces_invalid_values():
    assert normalize_version_code("20260715-1310") == "20260715-1310"
    assert normalize_version_code("unsafe") != "unsafe"
    assert normalize_version_code("20261340-9999") != "20261340-9999"


def test_render_pdf_has_pdf_signature():
    assert render_pdf([EVENT], "Show Cue Sheet").startswith(b"%PDF")


def test_render_pdf_supports_a4_portrait():
    assert render_pdf([EVENT], "Show Cue Sheet", "A4", "portrait").startswith(b"%PDF")


def test_pdf_and_preview_use_quarter_inch_sheet_margins():
    pdf_template, _, _ = env.loader.get_source(env, "cue_sheet.html")
    index_html = TestClient(app).get("/").text

    assert "@page { margin: 0.25in;" in pdf_template
    assert "body { margin: 0;" in pdf_template
    assert "aspect-ratio:11/8.5; padding:24px;" in index_html


def test_pdf_and_preview_use_content_aware_columns():
    pdf_template, _, _ = env.loader.get_source(env, "cue_sheet.html")
    index_html = TestClient(app).get("/").text

    assert "table-layout: auto;" in pdf_template
    assert "<colgroup>" not in pdf_template
    assert ".cue, .time, .duration { width: 1%;" in pdf_template
    assert "table-layout:auto;" in index_html
    assert ".col-cue, .col-time, .col-duration { width:1%;" in index_html
    assert 'td class="col-duration"' in index_html


def test_pdf_and_preview_overlay_alternating_rows():
    pdf_template, _, _ = env.loader.get_source(env, "cue_sheet.html")
    index_html = TestClient(app).get("/").text

    assert "tbody tr:nth-child(even) td { background-color: rgba(255, 255, 255, 0.05); }" in pdf_template
    assert "tbody tr:nth-child(even) td { background-color:rgba(255,255,255,.05); }" in index_html
    assert "tbody td:nth-child(even)" not in pdf_template
    assert "tbody td:nth-child(even)" not in index_html


def test_cue_colour_and_tint_are_print_safe():
    assert cue_colour("#339e4e") == "#339E4E"
    assert cue_tint("#339E4E") == "rgba(51, 158, 78, 0.15)"
    assert cue_colour("not-a-colour") == ""


def test_pdf_rows_use_black_text_with_colour_tint():
    html = env.get_template("cue_sheet.html").render(
        events=[EVENT],
        title="Colour test",
        generated_at="",
        include_notes=True,
        selected_fields=[],
    )

    assert 'style="color:#000000; background-color:rgba(51, 158, 78, 0.15)"' in html
    assert 'style="color:#339E4E;' not in html


def test_cue_notes_render_under_title_in_smaller_italic_text():
    html = env.get_template("cue_sheet.html").render(
        events=[EVENT],
        title="Notes test",
        generated_at="",
        include_notes=True,
        selected_fields=[],
    )
    index_html = TestClient(app).get("/").text

    assert '<td class="title"><div>Doors</div><div class="cue-note">House opens</div></td>' in html
    assert '<th>Notes</th>' not in html
    assert "font-size: 7pt; font-style: italic;" in html
    assert "Cue notes under titles" in index_html
    assert 'data-field="Notes"' not in index_html
    assert 'class="cue-note"' in index_html


def test_pdf_only_contains_selected_custom_fields():
    page = PdfReader(
        BytesIO(
            render_pdf(
                [EVENT],
                "Selected Fields",
                selected_custom_fields=["Video"],
            )
        )
    ).pages[0]
    text = page.extract_text()
    assert "VIDEO" in text and "Holding slide" in text
    assert "AUDIO" not in text and "Walk-in playlist" not in text


def test_preview_returns_ontime_project_title_and_available_fields(monkeypatch):
    async def fake_rundown(_base_url):
        return {
            "title": "WCTC Underestimated to Unstoppable",
            "rundown_title": "Fall Kick Off 2026",
            "events": [EVENT],
            "custom_fields": ["Audio", "Video"],
        }

    monkeypatch.setattr("app.main._get_rundown", fake_rundown)
    response = TestClient(app).post("/preview", data={"base_url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["title"] == "WCTC Underestimated to Unstoppable"
    assert response.json()["custom_fields"] == ["Audio", "Video"]


def test_index_includes_multipage_preview_controls():
    html = TestClient(app).get("/").text

    assert '>Import Cues</button>' in html
    assert 'class="field-option" draggable="true"' in html
    assert "input.name='selected_fields'" in html
    assert "fieldList.addEventListener('dragstart'" in html
    assert "function finishFieldDrag()" in html
    assert 'id="page-nav"' in html
    assert 'data-testid="previous-page"' in html
    assert 'data-testid="page-select"' in html
    assert 'data-testid="next-page"' in html
    assert "const PREVIEW_PAGE_SIZE" not in html
    assert "function paginateEvents(events)" in html
    assert "usedHeight+rowHeight>availableTableHeight" in html
    assert "table.tHead.getBoundingClientRect().height" in html
    assert 'style="color:#000000;background-color:${cueTint(colour)}"' in html
    assert 'style="color:${colour};background-color:' not in html
    assert "function versionCode(date=new Date())" in html
    assert "function pdfFilename(value,version)" in html
    assert "data.set('version_code',version)" in html
    assert "link.download=pdfFilename(title.value,version)" in html
    assert "link.download='cue-sheet.pdf'" not in html


def test_generate_accepts_repeated_selected_custom_fields(monkeypatch):
    async def fake_rundown(_base_url):
        return {
            "title": "WCTC Underestimated to Unstoppable",
            "rundown_title": "Fall Kick Off 2026",
            "events": [EVENT],
            "custom_fields": ["Audio", "Video"],
        }

    monkeypatch.setattr("app.main._get_rundown", fake_rundown)
    response = TestClient(app).post(
        "/generate",
        data={
            "base_url": "https://example.com",
            "title": "Fall Kick Off 2026",
            "include_notes": "true",
            "version_code": "20260715-1310",
            "selected_custom_fields": ["Audio", "Video"],
        },
    )

    text = PdfReader(BytesIO(response.content)).pages[0].extract_text()
    assert response.status_code == 200
    assert all(header in text for header in ("AUDIO", "VIDEO"))
    assert "NOTES" not in text
    assert "House opens" in text
    assert "Generated 2026-07-15 13:10" in text
    assert "20260715-1310" in text
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="Fall Kick Off 2026-CUESHEET-20260715-1310.pdf";'
    )


def test_generate_preserves_dragged_field_order(monkeypatch):
    async def fake_rundown(_base_url):
        return {
            "title": "WCTC Underestimated to Unstoppable",
            "rundown_title": "Fall Kick Off 2026",
            "events": [EVENT],
            "custom_fields": ["Audio", "Video"],
        }

    monkeypatch.setattr("app.main._get_rundown", fake_rundown)
    response = TestClient(app).post(
        "/generate",
        data={
            "base_url": "https://example.com",
            "title": "Fall Kick Off 2026",
            "fields_configured": "true",
            "include_notes": "true",
            "selected_fields": ["Video", "Audio"],
        },
    )

    text = PdfReader(BytesIO(response.content)).pages[0].extract_text()
    assert response.status_code == 200
    assert text.index("VIDEO") < text.index("AUDIO")
    assert "NOTES" not in text
    assert all(value in text for value in ("Holding slide", "House opens", "Walk-in playlist"))


def test_multipage_pdf_repeats_column_headers_and_version_code():
    events = [
        {**EVENT, "id": f"evt-{index}", "cue": str(index), "title": f"Cue {index}"}
        for index in range(60)
    ]
    pages = PdfReader(
        BytesIO(render_pdf(events, "Long Show Cue Sheet", version_code="20260715-1310"))
    ).pages

    assert len(pages) > 1
    for page in pages:
        text = page.extract_text()
        assert all(header in text for header in ("CUE", "START", "DURATION", "TITLE", "AUDIO", "VIDEO"))
        assert "NOTES" not in text
        assert "20260715-1310" in text
