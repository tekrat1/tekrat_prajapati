from pathlib import Path

from app.brand_guide import BrandGuide

GUIDE = BrandGuide.load(Path(__file__).resolve().parent.parent / "data" / "brand-guide.md")


def test_rule_ids_match_expectations():
    # validators.py hard-codes these ids; this test fails if the guide is renumbered.
    expect = {"1.2": "line break", "2.1": "40–90", "2.2": "emojis", "2.3": "call to action", "2.4": "product name",
              "2.5": "2 product features", "3.1": "medical", "3.2": "absolute", "3.3": "prices", "3.4": "sustainability",
              "3.5": "competitors", "4.1": "3 to 5", "4.2": "#LumoLiving", "4.3": "language", "4.4": "20 characters"}
    for rid, needle in expect.items():
        assert needle in GUIDE.by_id[rid].text, rid


def test_multiline_bullet_is_joined():
    assert "back pain" in GUIDE.by_id["3.1"].text


def test_pinned_and_retrieved():
    sel = {s.rule.id: s for s in GUIDE.select_for_post("voice warm friend address the reader directly Spanish")}
    assert sel["2.1"].selected_by == "pinned"
    assert sel["1.4"].selected_by == "retrieved"
