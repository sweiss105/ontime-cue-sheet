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
