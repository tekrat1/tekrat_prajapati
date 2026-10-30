"""Regex detectors for the forbidden-claim rules (brand guide section 3).

Used twice: (1) the guardrail screens the *request* before generation, and
(2) the validator screens the *generated caption* afterwards. Patterns cover
English, German and Spanish.
"""
from __future__ import annotations

import re

_F = re.IGNORECASE


def _c(p: str) -> re.Pattern[str]:
    return re.compile(p, _F)


CLAIM_PATTERNS: dict[str, re.Pattern[str]] = {
    # 3.1 medical / health claims
    "3.1": _c(
        r"\b(cure[sd]?|curing|heal(s|ed|ing)?|treat(s|ed|ing|ment)?(?!\s+(yourself|yourselves|your|you)\b)|"
        r"prevent(s|ed|ing)?|insomnia|anxiety|depress\w*|back\s?pain|pain\s?relief|relieves?\s+(pain|stress|anxiety)|"
        r"therap\w+|clinically|medical\w*|health\s+benefits?|detox\w*|sleep\s+better|better\s+sleep|"
        r"helps?\s+(you\s+)?(to\s+)?sleep|(reduces?|lowers?)\s+stress|stress\s+relief|"
        r"heilt|heilen|heilung|kuriert|behandelt|behandlung|verhindert|vorbeugt|vorbeugen|schlaflosigkeit|"
        r"angststörung|angstzustände|rückenschmerzen|depression\w*|lindert|linderung|therap\w+|"
        r"besser\s+schlafen|besserer\s+schlaf|stress\s+abbau\w*|"
        r"cura(r|s|n)?\b|curativ\w+|sana(r|s|n)?\b|(?<!se\s)trata(r|s|n|miento)?\b|previene|prevenir|insomnio|"
        r"ansiedad|dolor\s+de\s+espalda|depresión|alivia(r|s|n)?\b|terapéutic\w+|terapia|"
        r"dormir\s+mejor|mejor(a|ar)?\s+(el\s+)?sueño)"
    ),
    # 3.2 absolute claims
    "3.2": _c(
        r"(\b(best|perfect(ly)?|guarantee[ds]?|"
        r"beste[rnms]?|perfekt\w*|garantiert\w*|"
        r"mejor(es)?|perfect[oa]s?|perfectamente|garantizad[oa]s?|garantía)\b|100\s?%)"
    ),
    # 3.3 prices, discounts, limited-time offers
    "3.3": _c(
        r"([€$£]|\d+[.,]?\d*\s?(€|eur\b|euros?\b|gbp\b|usd\b|pesos\b|mxn\b|£|\$)|"
        r"\d+\s?%\s?(off|rabatt|dto|descuento)|"
        r"\b(discounts?|on sale|special offer|deal|free shipping|limited[\s-]time|limited edition|"
        r"price|prices|cheap|"
        r"rabatt\w*|angebot\w*|aktion|gratis versand|kostenloser versand|zeitlich begrenzt|preis\w*|"
        r"descuento\w*|oferta\w*|rebajas|tiempo limitado|envío gratis|precio\w*)\b)"
    ),
    # 3.4 sustainability claims
    "3.4": _c(
        r"\b(sustainab\w*|eco[\s-]?friendly|eco\b|environment\w*|planet|recycl\w*|biodegrad\w*|carbon|"
        r"organic|ethical\w*|zero[\s-]waste|green(er)?\s+(choice|living)|"
        r"nachhaltig\w*|umweltfreundlich\w*|ökologisch\w*|recycel\w*|klimaneutral\w*|"
        r"sostenib\w*|ecológic\w*|ecolog\w*|respetuos[oa]\s+con\s+(el\s+)?(medio\s+ambiente|planeta)|reciclad\w*)\b"
    ),
    # 3.5 competitors
    "3.5": _c(
        r"\b(ikea|zara\s+home|h&m\s+home|muji|westwing|maisons?\s+du\s+monde|ferm\s+living|jysk|kave\s+home|"
        r"la\s+redoute|john\s+lewis|dunelm|diptyque|jo\s+malone|yankee\s+candle|lululemon|manduka|dyson|"
        r"competitors?|rivals?|other\s+brands?|better\s+than|unlike\s+(other|the)\s+\w+|"
        r"konkurrenz|konkurrent\w*|besser\s+als|andere\s+marken|"
        r"competencia|competidor\w*|mejor\s+que|otras\s+marcas)\b"
    ),
}

RULE_LABELS = {
    "3.1": "medical or health claim",
    "3.2": "absolute claim (best / perfect / guaranteed / 100%)",
    "3.3": "price, discount or limited-time offer",
    "3.4": "sustainability claim",
    "3.5": "competitor mention",
}

# Explanation + compliant alternative shown to the requester on refusal.
ALTERNATIVES = {
    "3.1": "Describe how the product looks or feels instead (for example warm light for slow evenings).",
    "3.2": "Use specific, honest details instead of superlatives (for example the real run time or material).",
    "3.3": "Supply the exact offer details in the request notes (amount and dates) and it can be mentioned.",
    "3.4": "Only the product's own sustainability field can be used; this product has none, so leave it out.",
    "3.5": "Talk about what makes the Lumo product itself nice to use, without naming other brands.",
}
