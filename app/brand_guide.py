"""Brand-guide parsing and retrieval.

The guide is split into one chunk per rule (a bullet or a standalone paragraph),
each with a stable id such as "2.1" (section 2, rule 1). Retrieval is BM25 over
those chunks, implemented in pure Python so there is nothing to download.

Design decision: sections 2-4 (caption format, forbidden claims, hashtags) are
PINNED. They are hard constraints that are also machine-checked after generation,
so compliance never depends on retrieval recall. The softer guidance (voice,
language style, video, visual) is RETRIEVED by relevance to the request.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

PINNED_SECTIONS = {2, 3, 4}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "per", "that", "the", "to", "with", "not", "no", "e", "g",
}
_TOKEN_RE = re.compile(r"[a-zäöüß0-9]+")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


@dataclass(frozen=True)
class Rule:
    id: str
    section_no: int
    section: str
    text: str

    @property
    def chunk_text(self) -> str:
        return f"{self.section}. {self.text}"


@dataclass(frozen=True)
class SelectedRule:
    rule: Rule
    selected_by: str  # "pinned" | "retrieved"
    score: float


class BrandGuide:
    def __init__(self, rules: list[Rule]):
        self.rules = rules
        self.by_id = {r.id: r for r in rules}
        self._docs = [tokenize(r.chunk_text) for r in rules]
        self._avgdl = sum(len(d) for d in self._docs) / max(len(self._docs), 1)
        df: Counter[str] = Counter()
        for d in self._docs:
            df.update(set(d))
        n = len(self._docs)
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    # ---- parsing -------------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> "BrandGuide":
        rules: list[Rule] = []
        section_no, section, counter = 0, "", 0
        buf: list[str] = []
        kind = None  # "bullet" | "para"

        def flush() -> None:
            nonlocal buf, kind, counter
            if buf and section_no:
                counter += 1
                text = " ".join(s.strip() for s in buf).strip()
                rules.append(Rule(f"{section_no}.{counter}", section_no, section, text))
            buf, kind = [], None

        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^##\s+(\d+)\.\s+(.*)$", line)
            if m:
                flush()
                section_no, section, counter = int(m.group(1)), m.group(2).strip(), 0
                continue
            if line.startswith("# "):
                flush()
                continue
            if not line.strip():
                flush()
                continue
            if line.startswith("- "):
                flush()
                buf, kind = [line[2:]], "bullet"
            elif kind == "bullet" and line.startswith(" "):
                buf.append(line)  # continuation of a bullet
            else:
                if kind == "bullet":
                    flush()
                buf.append(line)
                kind = "para"
        flush()
        return cls(rules)

    # ---- retrieval -----------------------------------------------------
    def bm25(self, query: str) -> list[float]:
        q = tokenize(query)
        k1, b = 1.5, 0.75
        scores = []
        for doc in self._docs:
            tf = Counter(doc)
            s = 0.0
            for term in set(q):
                if term not in tf:
                    continue
                f = tf[term]
                s += self._idf.get(term, 0.0) * f * (k1 + 1) / (f + k1 * (1 - b + b * len(doc) / self._avgdl))
            scores.append(s)
        return scores

    def select_for_post(self, query: str, min_score: float = 2.0, top_k: int = 6) -> list[SelectedRule]:
        scores = self.bm25(query)
        selected: list[SelectedRule] = []
        retrieved: list[SelectedRule] = []
        for rule, score in zip(self.rules, scores):
            if rule.section_no in PINNED_SECTIONS:
                selected.append(SelectedRule(rule, "pinned", round(score, 3)))
            elif score >= min_score:
                retrieved.append(SelectedRule(rule, "retrieved", round(score, 3)))
        retrieved.sort(key=lambda s: -s.score)
        selected.extend(retrieved[:top_k])
        selected.sort(key=lambda s: tuple(int(x) for x in s.rule.id.split(".")))
        return selected
