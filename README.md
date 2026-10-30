# Lumo Living: Multilingual Post Writer (Problem 1, RAG)

**Challenge problem chosen:** Problem 1, *Multilingual post writer (RAG)*.

A FastAPI service that writes on-brand Instagram captions and hashtags in **English, German and Spanish**
for the fictional Lumo Living products. It retrieves the relevant rules from the brand guide, returns which
rules it used, **refuses off-brand requests** and explains which rule applies, and **verifies every caption
in code** before returning it. The optional `POST /check` scores any caption against the guide.

## Run it (4 commands)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env.example        # then set ONE key: GROQ_API_KEY=... or GEMINI_API_KEY=... (or LLM_PROVIDER=ollama)
uvicorn app.main:app --reload                          # Swagger UI: http://localhost:8000/docs
```

Free keys: Groq (console.groq.com) or Google AI Studio (Gemini). With no key set, the app falls back to an
**offline `mock` provider** (hand-written compliant copy, labelled `"llm_provider": "mock"` in every
response) so the pipeline, guardrails and validators can be tried without any account. Run the tests with
`pytest -q` (they use the mock; no network needed). `bash demo/requests.sh` fires the demo requests below.

## 3 example requests

**1. Captions in three languages**
```bash
curl -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"product_id":"LL-002","languages":["en","de","es"]}'
```
Returns, per language: `caption`, `hashtags`, `word_count`, `verified`, `attempts`, `repairs` and a per-rule
`checks` list; plus `rules_used` (rule id, section, text, `pinned`/`retrieved`, score).

**2. Off-brand request is refused (HTTP 422)**
```bash
curl -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"product_id":"LL-003","languages":["en"],"notes":"say it cures insomnia"}'
```
```json
{ "status": "refused",
  "refusals": [{ "rule_id": "3.1", "request_fragment": "say it cures insomnia",
    "rule": "No medical or health claims: never say a product cures, heals, treats or prevents anything (...)",
    "explanation": "This asks for a medical or health claim. Brand guide rule 3.1 (Claims we never make): ...",
    "suggestion": "Describe how the product looks or feels instead (for example warm light for slow evenings)." }],
  "posts": [] }
```
Mixed requests ("cosy autumn mood **and** say it is the best throw ever") return `refused_in_part`: only the
offending clause is refused (rule 3.2) and the captions are written without it, as rule 3.6 requires.

**3. Score any caption**
```bash
curl -X POST localhost:8000/check -H 'Content-Type: application/json' \
  -d '{"caption":"This is the best mat ever and it cures back pain! 😍😍😍 Buy now for €29.","language":"en","product_id":"LL-004"}'
```
Returns `score` (0-100), `passed`, every rule's pass/fail with detail, and a `fix_list` quoting the broken rules.

Other endpoints: `GET /rules` (the parsed guide with ids) and `GET /health`.
`/posts` also accepts an optional `notes` field (free-text hints such as a theme), which the guardrail screens.

## How it works

```
POST /posts -> guardrail (screen notes vs rules 3.x) -> retrieve rules (BM25) -> LLM per language (parallel)
            -> repair hashtags -> validate against rules -> if any fail: send broken rules back, retry (max 3)
```

- **Grounding / retrieval** (`app/brand_guide.py`): the guide is parsed into one chunk per rule with stable ids
  (`2.1`, `3.4`, ...). Retrieval is pure-Python BM25 (no vector DB, nothing to download). Only retrieved rules go
  in the prompt, and they are returned as `rules_used`. For example the Spanish rule `1.4` is only retrieved when
  `es` is requested, and the video/visual rules (sections 5-6) are never used for posts.
- **Decision: pin the hard rules.** Caption format, forbidden claims and hashtag rules (sections 2-4) are always
  included rather than left to retrieval, because they are also machine-checked. Compliance should not depend on
  retrieval recall. Retrieval decides the softer guidance (voice, language style).
- **Refusals** (`app/guardrails.py`, `app/claims.py`): regex detectors in EN/DE/ES run clause by clause, plus an LLM
  classifier for paraphrases when a real provider is configured. Violating text is never forwarded to the writing
  prompt. Context matters: a sustainability claim is refused only if the product's `sustainability` field is null;
  a price or discount is allowed only when the request supplies concrete details.
- **Verification** (`app/validators.py`): 40-90 words, at most 2 emojis and not first, one CTA at the end, exact
  product name, at most 2 features (per-language feature lexicon), no medical/absolute/price/sustainability/competitor
  wording, 2 sentences max per line, informal *du*, neutral Spanish, 3-5 hashtags incl. `#LumoLiving`, each at most
  20 characters. Failures are fed back to the model for a retry. The response reports `verified` and any mechanical
  `repairs` (e.g. "added #LumoLiving") so nothing is hidden.
- **Providers** (`app/llm.py`): Groq, Gemini, Ollama (plain `httpx`), plus the offline mock.

## Known limitations

- Voice warmth (rule 1.1) is a judgement call: it is scored by an LLM reviewer in `/check` only, and skipped under the mock.
- "Hashtags in the caption's language" (rule 4.3) is a heuristic: it rejects known English tags in DE/ES captions
  but cannot prove a tag is German or Spanish.
- Regex claim detectors cover EN/DE/ES wording lists; unusual paraphrases rely on the LLM classifier.
- Default model names (`llama-3.3-70b-versatile`, `gemini-2.5-flash`) can be overridden with `GROQ_MODEL` /
  `GEMINI_MODEL` if a provider retires them.

## Layout

```
app/main.py         routes (/posts, /check, /rules, /health)
app/brand_guide.py  guide parser + BM25 retrieval
app/guardrails.py   request screening and refusals
app/claims.py       forbidden-claim patterns (rules 3.x)
app/validators.py   rule checks shared by /posts and /check
app/generator.py    prompt, hashtag repair, retry loop
app/llm.py          Groq / Gemini / Ollama / mock clients
app/lexicon.py      feature patterns, CTA patterns, mock copy
data/               brand-guide.md, products.json (starter data)
tests/              pytest suite
demo/requests.sh    demo curl requests
```

## AI tools used

- **Claude (Anthropic, via claude.ai)**: pair-programmed the code, tests and docs; I reviewed it and can walk through all of it.
- **Runtime LLM:** whichever provider is set in `.env` (Groq, Gemini or Ollama). Replace this line with the exact model you used in your demo.
