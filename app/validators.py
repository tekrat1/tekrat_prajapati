"""Deterministic brand-guide checks, shared by POST /posts (verify generated
captions) and POST /check (score any caption). Each check is tied to a rule id
from data/brand-guide.md."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

from .claims import CLAIM_PATTERNS
from .lexicon import (
    ADDRESS_PATTERNS, CTA_LINK_PATTERNS, CTA_PATTERNS, ENGLISH_HASHTAGS,
    FEATURE_PATTERNS, SPANISH_NON_NEUTRAL,
)

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2190-\u21FF]"
)
HASHTAG_RE = re.compile(r"#\w+", re.UNICODE)
_ABBREV_RE = re.compile(r"\b(ca|z\.\s?B|bzw|etc|usw|Nr)\.", re.IGNORECASE)


@dataclass
class Check:
    rule_id: str
    name: str
    status: str  # "pass" | "fail" | "skipped"
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------- text helpers
def split_caption(text: str) -> tuple[str, list[str]]:
    """Split a full caption into (body, hashtags)."""
    tags = HASHTAG_RE.findall(text)
    body = HASHTAG_RE.sub("", text)
    body = "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in body.splitlines())
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body, tags


def hashtags_at_end(text: str) -> bool:
    m = HASHTAG_RE.search(text)
    if not m:
        return True
    rest = HASHTAG_RE.sub("", text[m.start():])
    return not re.search(r"\w", rest)


def count_words(body: str) -> int:
    clean = EMOJI_RE.sub(" ", body)
    return sum(1 for tok in clean.split() if re.search(r"\w", tok))


def sentences(line: str) -> list[str]:
    line = _ABBREV_RE.sub(lambda m: m.group(0).rstrip("."), line)
    parts = re.split(r"(?<=[.!?…])\s+", line.strip())
    return [p for p in parts if re.search(r"\w", p)]


def strip_product_name(text: str, product: dict | None) -> str:
    return text.replace(product["name"], " ") if product else text


# ---------------------------------------------------------------- the checks
def check_caption(
    body: str,
    hashtags: list[str],
    *,
    language: str,
    product: dict | None = None,
    allow_offer: bool = False,
    full_text: str | None = None,
) -> list[Check]:
    checks: list[Check] = []
    add = lambda rid, name, ok, detail, skip=False: checks.append(  # noqa: E731
        Check(rid, name, "skipped" if skip else ("pass" if ok else "fail"), detail)
    )
    lines = [ln for ln in body.split("\n") if ln.strip()]
    sents_all = [s for ln in lines for s in sentences(ln)]

    # 1.2 short sentences / max 2 sentences per line
    worst = max((len(sentences(ln)) for ln in lines), default=0)
    add("1.2", "Max 2 sentences before a line break", worst <= 2,
        f"longest line has {worst} sentence(s)")

    # 1.3 direct address, informal du
    addr = re.search(ADDRESS_PATTERNS[language], body, re.IGNORECASE)
    formal = False
    if language == "de":
        for s in sents_all:
            toks = re.findall(r"[A-Za-zÄÖÜäöüß]+", s)[1:]
            if any(t in ("Sie", "Ihnen") or re.fullmatch(r"Ihr(e|en|em|er|es)?", t) for t in toks):
                formal = True
    add("1.3", "Addresses the reader directly (informal du in German)",
        bool(addr) and not formal,
        "formal Sie/Ihnen found" if formal else ("direct address found" if addr else "no direct address found"))

    # 1.4 neutral Spanish
    if language == "es":
        bad = re.findall(SPANISH_NON_NEUTRAL, body, re.IGNORECASE)
        add("1.4", "Neutral Spanish (Spain + Mexico)", not bad,
            f"regional words: {sorted(set(bad))}" if bad else "no regional words found")
    else:
        add("1.4", "Neutral Spanish (Spain + Mexico)", True, "not a Spanish caption", skip=True)

    # 2.1 length
    wc = count_words(body)
    add("2.1", "40-90 words", 40 <= wc <= 90, f"{wc} words")

    # 2.2 emojis
    n_emoji = len(EMOJI_RE.findall(body))
    starts = bool(body) and bool(EMOJI_RE.match(body.lstrip()))
    add("2.2", "Max 2 emojis, never at the start", n_emoji <= 2 and not starts,
        f"{n_emoji} emoji(s); starts with emoji: {starts}")

    # 2.3 CTA
    last = sentences(lines[-1])[-1] if lines else ""
    has_cta = bool(re.search(CTA_PATTERNS[language], last, re.IGNORECASE))
    n_link = len(re.findall(CTA_LINK_PATTERNS[language], body, re.IGNORECASE))
    add("2.3", "Ends with exactly one call to action", has_cta and n_link <= 1,
        f"last sentence: {last!r}" if has_cta else f"no call to action in last sentence: {last!r}")

    # 2.4 / 2.5 product name and features
    if product:
        add("2.4", "Product name exactly as in products.json", product["name"] in body,
            f"expects {product['name']!r}")
        pats = FEATURE_PATTERNS.get(product["id"])
        if pats:
            text = strip_product_name(body, product)
            hit = [i for i, p in enumerate(pats) if re.search(p[language], text, re.IGNORECASE)]
            feats = [product["features"][i] for i in hit]
            add("2.5", "At most 2 product features", len(hit) <= 2,
                f"mentions {len(hit)} feature(s): {feats}")
        else:
            add("2.5", "At most 2 product features", True, "no feature lexicon for product", skip=True)
    else:
        add("2.4", "Product name exactly as in products.json", True, "no product_id given", skip=True)
        add("2.5", "At most 2 product features", True, "no product_id given", skip=True)

    # 3.x forbidden claims
    def claim(rid: str, name: str, skip_reason: str | None = None) -> None:
        if skip_reason:
            add(rid, name, True, skip_reason, skip=True)
            return
        # product name is exempt (e.g. "Fig & Cedar" can never trigger a claim)
        found = [m.group(0) for m in CLAIM_PATTERNS[rid].finditer(strip_product_name(body, product))]
        add(rid, name, not found, f"found: {sorted(set(f.lower() for f in found))}" if found else "none found")

    claim("3.1", "No medical or health claims")
    claim("3.2", "No absolute claims")
    claim("3.3", "No prices/discounts/limited-time offers",
          "offer details were given in the request" if allow_offer else None)
    if product is None:
        found = CLAIM_PATTERNS["3.4"].findall(body)
        add("3.4", "No unsupported sustainability claims", not found,
            "sustainability wording found but no product_id given to verify it" if found else "none found")
    elif product.get("sustainability"):
        add("3.4", "No unsupported sustainability claims", True,
            "product has a sustainability field; claims must stick to it", skip=True)
    else:
        claim("3.4", "No unsupported sustainability claims")
    claim("3.5", "No competitor mentions")

    # 4.x hashtags
    tags = hashtags
    ok_count = 3 <= len(tags) <= 5
    add("4.1", "3-5 hashtags, at the end", ok_count and hashtags_at_end(full_text or body + " " + " ".join(tags)),
        f"{len(tags)} hashtag(s)")
    add("4.2", "Includes #LumoLiving", any(t.lower() == "#lumoliving" for t in tags),
        "present" if any(t.lower() == "#lumoliving" for t in tags) else "missing")
    local = [t for t in tags if t.lower() != "#lumoliving"]
    if language == "en":
        add("4.3", "Hashtags in the caption's language", True, "English caption", skip=True)
    else:
        eng = [t for t in local if t.lower() in ENGLISH_HASHTAGS]
        add("4.3", "Hashtags in the caption's language", bool(local) and not eng,
            f"English hashtags in a {language} caption: {eng}" if eng else
            ("ok" if local else "no local-language hashtag"))
    long_tags = [t for t in tags if len(t) > 20]
    add("4.4", "No hashtag longer than 20 characters", not long_tags,
        f"too long: {long_tags}" if long_tags else "ok")
    return checks


def check_full_text(text: str, **kw: Any) -> list[Check]:
    body, tags = split_caption(text)
    return check_caption(body, tags, full_text=text, **kw)


def failures(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.status == "fail"]


def score(checks: list[Check]) -> int:
    graded = [c for c in checks if c.status != "skipped"]
    return round(100 * sum(c.passed for c in graded) / len(graded)) if graded else 0
