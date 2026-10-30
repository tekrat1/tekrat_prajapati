"""Thin LLM client layer: Groq, Gemini, Ollama, plus an offline mock.

Every provider exposes `async complete_json(system, messages, meta)` and returns a
parsed JSON dict. `meta` is only read by the mock (it needs to know the task).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import httpx

from .config import Settings, get_settings
from .lexicon import CATEGORY_HASHTAGS, MOCK_COPY, MOCK_CTA

log = logging.getLogger("lumo.llm")
Message = dict[str, str]  # {"role": "user" | "assistant", "content": str}


class LLMError(RuntimeError):
    pass


def parse_json(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output, tolerating code fences / chatter."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMError(f"Model did not return valid JSON: {text[:200]!r}")


async def _post(client: httpx.AsyncClient, url: str, *, retries: int = 2, **kw: Any) -> dict[str, Any]:
    last = ""
    for attempt in range(retries + 1):
        try:
            r = await client.post(url, **kw)
        except httpx.HTTPError as exc:
            last = f"{type(exc).__name__}: {exc}"
        else:
            if r.status_code < 400:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code not in (429, 500, 502, 503, 504):
                break
        await asyncio.sleep(1.5 * (attempt + 1))
    raise LLMError(last)


class Provider:
    name = "base"
    model = ""
    is_mock = False

    async def complete_json(self, system: str, messages: list[Message], meta: dict | None = None) -> dict:
        raise NotImplementedError


class GroqProvider(Provider):
    name = "groq"

    def __init__(self, s: Settings):
        if not s.groq_api_key:
            raise LLMError("GROQ_API_KEY is not set")
        self.key, self.model = s.groq_api_key, s.groq_model

    async def complete_json(self, system, messages, meta=None):
        body = {
            "model": self.model,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, *messages],
        }
        async with httpx.AsyncClient(timeout=60) as c:
            data = await _post(c, "https://api.groq.com/openai/v1/chat/completions",
                               headers={"Authorization": f"Bearer {self.key}"}, json=body)
        return parse_json(data["choices"][0]["message"]["content"])


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self, s: Settings):
        if not s.gemini_api_key:
            raise LLMError("GEMINI_API_KEY is not set")
        self.key, self.model = s.gemini_api_key, s.gemini_model

    async def complete_json(self, system, messages, meta=None):
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages
            ],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=60) as c:
            data = await _post(c, url, headers={"x-goog-api-key": self.key}, json=body)
        try:
            return parse_json(data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Gemini response: {str(data)[:300]}") from exc


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, s: Settings):
        self.host, self.model = s.ollama_host, s.ollama_model

    async def complete_json(self, system, messages, meta=None):
        body = {
            "model": self.model, "stream": False, "format": "json",
            "options": {"temperature": 0.7},
            "messages": [{"role": "system", "content": system}, *messages],
        }
        async with httpx.AsyncClient(timeout=180) as c:
            data = await _post(c, f"{self.host}/api/chat", json=body, retries=0)
        return parse_json(data["message"]["content"])


class MockProvider(Provider):
    """Offline provider for tests and key-less demos. NOT an LLM: it returns
    hand-written, rule-compliant copy so the whole pipeline can run end to end."""

    name = "mock"
    model = "offline-templates"
    is_mock = True

    async def complete_json(self, system, messages, meta=None):
        meta = meta or {}
        task = meta.get("task")
        if task == "guardrail":
            return {"violations": []}
        if task == "review":
            return {"passes": True, "feedback": "mock provider: voice not reviewed"}
        pid, lang, product = meta["product_id"], meta["language"], meta["product"]
        p1, p2 = MOCK_COPY[(pid, lang)]
        caption = "\n\n".join([p1, p2.format(name=product["name"]), MOCK_CTA[lang]])
        cat = CATEGORY_HASHTAGS[product["category"]][lang]
        local = {"en": ["#SlowLiving", "#CosyHome"], "de": ["#Wohnideen", "#Zuhause"], "es": ["#HogarAcogedor", "#Decoración"]}[lang]
        return {"caption": caption, "hashtags": ["#LumoLiving", cat, *local]}


def get_provider() -> Provider:
    s = get_settings()
    providers = {"groq": GroqProvider, "gemini": GeminiProvider, "ollama": OllamaProvider, "mock": lambda _s: MockProvider()}
    if s.provider not in providers:
        raise LLMError(f"Unknown LLM_PROVIDER {s.provider!r}; use one of {sorted(providers)}")
    return providers[s.provider](s)
