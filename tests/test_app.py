from io import BytesIO

from pypdf import PdfReader

from app.ontime import build_rundown_url, extract_events
from app.pdf import clock, render_pdf


EVENT = {
    "type": "event",
    "id": "evt-1",
    "cue": "A1",
    "title": "Doors",
    "note": "House opens",
    "timeStart": 36_000_000,
    "duration": 1_800_000,
    "custom": {"Audio": "Walk-in playlist"},
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


def test_clock_formats_milliseconds():
    assert clock(36_061_000) == "10:01:01"


def test_render_pdf_has_pdf_signature():
    assert render_pdf([EVENT], "Show Cue Sheet").startswith(b"%PDF")


def test_render_pdf_supports_a4_portrait():
    assert render_pdf([EVENT], "Show Cue Sheet", "A4", "portrait").startswith(b"%PDF")


def test_multipage_pdf_repeats_column_headers():
    events = [
        {**EVENT, "id": f"evt-{index}", "cue": str(index), "title": f"Cue {index}"}
        for index in range(60)
    ]
    pages = PdfReader(BytesIO(render_pdf(events, "Long Show Cue Sheet"))).pages

    assert len(pages) > 1
    for page in pages:
        text = page.extract_text()
        assert all(header in text for header in ("CUE", "START", "DURATION", "TITLE", "NOTES", "CUSTOM FIELDS"))
