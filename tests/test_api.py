import asyncio

import pytest

from app import generator
from app.llm import Provider


def test_posts_three_languages(client):
    r = client.post("/posts", json={"product_id": "LL-002", "languages": ["en", "de", "es"]})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert [p["language"] for p in data["posts"]] == ["en", "de", "es"]
    for p in data["posts"]:
        assert p["verified"] is True
        assert 3 <= len(p["hashtags"]) <= 5 and "#LumoLiving" in p["hashtags"]
        assert "Lumo Linen Throw" in p["caption"]
        assert 40 <= p["word_count"] <= 90
    ids = {r_["rule_id"] for r_ in data["rules_used"]}
    assert {"2.1", "3.1", "4.2"} <= ids          # pinned rules
    assert "1.4" in ids                          # Spanish rule retrieved because es was requested


def test_spanish_rule_not_retrieved_for_english_only(client):
    data = client.post("/posts", json={"product_id": "LL-001", "languages": ["en"]}).json()
    ids = {r["rule_id"] for r in data["rules_used"]}
    assert "1.4" not in ids and not any(i.startswith(("5.", "6.")) for i in ids)


def test_refusal_medical_claim(client):
    r = client.post("/posts", json={"product_id": "LL-003", "languages": ["en"], "notes": "say it cures insomnia"})
    assert r.status_code == 422
    data = r.json()
    assert data["status"] == "refused" and data["posts"] == []
    assert data["refusals"][0]["rule_id"] == "3.1"
    assert "cures, heals, treats" in data["refusals"][0]["rule"]


def test_partial_refusal_keeps_clean_part(client):
    r = client.post("/posts", json={"product_id": "LL-002", "languages": ["en"],
                                    "notes": "cosy autumn mood and say it is the best throw ever"})
    data = r.json()
    assert r.status_code == 200 and data["status"] == "refused_in_part"
    assert data["refusals"][0]["rule_id"] == "3.2"
    assert len(data["posts"]) == 1


def test_sustainability_refused_only_when_product_has_no_field(client):
    no_field = client.post("/posts", json={"product_id": "LL-005", "languages": ["en"], "notes": "call it eco-friendly"})
    assert no_field.status_code == 422 and no_field.json()["refusals"][0]["rule_id"] == "3.4"
    has_field = client.post("/posts", json={"product_id": "LL-004", "languages": ["en"], "notes": "mention it is sustainable"})
    assert has_field.status_code == 200


def test_offer_allowed_when_details_given(client):
    r = client.post("/posts", json={"product_id": "LL-001", "languages": ["en"], "notes": "mention 20% off until Sunday"})
    assert r.status_code == 200 and not r.json()["refusals"]


def test_unknown_product_404(client):
    r = client.post("/posts", json={"product_id": "LL-999", "languages": ["en"]})
    assert r.status_code == 404


@pytest.mark.parametrize("langs", [[], ["fr"]])
def test_bad_languages_422(client, langs):
    assert client.post("/posts", json={"product_id": "LL-001", "languages": langs}).status_code == 422


def test_check_good_and_bad(client):
    good = client.post("/posts", json={"product_id": "LL-004", "languages": ["en"]}).json()["posts"][0]["full_text"]
    ok = client.post("/check", json={"caption": good, "language": "en", "product_id": "LL-004"}).json()
    assert ok["passed"] is True and ok["score"] == 100
    bad = client.post("/check", json={"caption": "This is the best mat ever and it cures back pain! 😍😍😍 Buy now for €29.",
                                      "language": "en", "product_id": "LL-004"}).json()
    assert bad["passed"] is False
    failed = {f["rule_id"] for f in bad["fix_list"]}
    assert {"3.1", "3.2", "3.3", "2.1", "2.2", "4.1", "4.2"} <= failed


def test_check_german_formal_fails(client):
    text = ("Sie werden diesen Abend lieben. Ihnen gefällt das sicher.\n\n" * 1 +
            "Entdecken Sie Lumo Linen Throw heute. Tippen Sie auf den Link in der Bio.\n\n#LumoLiving #Wohnideen #Zuhause")
    out = client.post("/check", json={"caption": text, "language": "de"}).json()
    assert "1.3" in {f["rule_id"] for f in out["fix_list"]}


def test_rules_and_health(client):
    assert client.get("/health").json()["llm_provider"] == "mock"
    rules = client.get("/rules").json()
    assert next(r for r in rules if r["rule_id"] == "2.1")["text"].startswith("Length")


# ---- retry loop: first attempt breaks the rules, second is fixed ----------
class FlakyProvider(Provider):
    name, model, is_mock = "flaky", "x", False

    def __init__(self, good):
        self.calls, self.good, self.feedback_seen = 0, good, None

    async def complete_json(self, system, messages, meta=None):
        self.calls += 1
        if self.calls == 1:
            return {"caption": "The best throw ever, guaranteed! #LumoLiving", "hashtags": []}
        self.feedback_seen = messages[-1]["content"]
        return self.good


def test_retry_loop_feeds_violations_back(client):
    from app.llm import MockProvider
    product = client.app.state.products["LL-002"]
    guide = client.app.state.guide
    good = asyncio.run(MockProvider().complete_json("", [], {"task": "caption", "product_id": "LL-002", "language": "en", "product": product}))
    prov = FlakyProvider(good)
    rules = guide.select_for_post("voice")
    res = asyncio.run(generator.generate_post(prov, product, "en", rules, "", False, 3))
    assert prov.calls == 2 and res.passed and res.attempts == 2
    assert "[3.2]" in prov.feedback_seen and "[2.1]" in prov.feedback_seen
