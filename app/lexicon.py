"""Language data used by validators and by the offline mock provider.

FEATURE_PATTERNS: per product, one regex per feature (same order as products.json)
and per language. Used to count how many features a caption mentions (rule 2.5).
"""
from __future__ import annotations

FEATURE_PATTERNS: dict[str, list[dict[str, str]]] = {
    "LL-001": [
        {"en": r"hand-?glaz|glazed", "de": r"glasier|glasur", "es": r"esmalt"},
        {"en": r"350\s?ml", "de": r"350\s?ml", "es": r"350\s?ml"},
        {"en": r"dishwasher", "de": r"spülmaschine", "es": r"lavavajillas"},
        {"en": r"set of 4|four colou?rs|4 colou?rs", "de": r"4er|set aus 4|vier farben|4 farben", "es": r"set de 4|cuatro colores|4 colores"},
    ],
    "LL-002": [
        {"en": r"stone-?washed", "de": r"stone-?washed|vorgewaschen", "es": r"lavado a la piedra|stone-?washed|prelavado"},
        {"en": r"130\s?[x×]\s?170", "de": r"130\s?[x×]\s?170", "es": r"130\s?[x×]\s?170"},
        {"en": r"softer", "de": r"weicher", "es": r"más suave|mas suave|suaviza"},
        {"en": r"\boat\b|charcoal", "de": r"hafer|anthrazit", "es": r"avena|carbón|antracita"},
    ],
    "LL-003": [
        {"en": r"ceramic", "de": r"keramik", "es": r"cerámic|ceramic"},
        {"en": r"\b8\s?(hours|hrs|h)\b|eight hours", "de": r"\b8\s?(stunden|std)|acht stunden", "es": r"\b8\s?horas|ocho horas"},
        {"en": r"ambient|warm light|warm glow", "de": r"ambiente|warmes licht|warmen licht", "es": r"luz ambiental|luz cálida"},
        {"en": r"shut-?off|auto-?off|turns itself off|switches itself off", "de": r"abschalt|ausschalt", "es": r"apagado automático|se apaga"},
    ],
    "LL-004": [
        {"en": r"cork", "de": r"kork", "es": r"corcho"},
        {"en": r"grip|wet\b", "de": r"rutschfest|nässe|nass\b|griffig", "es": r"agarre|mojad|antidesliz"},
        {"en": r"\b4\s?mm", "de": r"\b4\s?mm", "es": r"\b4\s?mm"},
        {"en": r"strap", "de": r"tragegurt|gurt", "es": r"correa"},
    ],
    "LL-005": [
        {"en": r"\bsoy", "de": r"soja", "es": r"soja"},
        {"en": r"45\s?(hours|hrs)", "de": r"45\s?(stunden|std)", "es": r"45\s?horas"},
        {"en": r"glass jar|reusable", "de": r"wiederverwend|\bglas\b", "es": r"reutiliz|vidrio"},
        {"en": r"wick", "de": r"docht", "es": r"mecha"},
    ],
}

# Call-to-action detection (rule 2.3): the last sentence must contain one of these.
CTA_PATTERNS = {
    "en": r"\b(tap|click|visit|shop|discover|see|check out|find out|learn|order|explore|swipe|dm|message|follow|link in (my |our |the )?bio)\b",
    "de": r"(tipp|klick|entdeck|besuch|shop|schau|sieh|erfahr|bestell|folg|speicher|link in (der )?bio)",
    "es": r"(toca|pulsa|haz clic|descubre|visita|mira|conoce|compra|pide|explora|sigue|guarda|enlace|link en)",
}
CTA_LINK_PATTERNS = {
    "en": r"link in (my |our |the )?bio",
    "de": r"link in (der )?bio",
    "es": r"(enlace|link) (en|de) (la )?bio",
}

# Direct address (rule 1.3)
ADDRESS_PATTERNS = {
    "en": r"\byou(r|rs|rself|'ll|'re|'ve|'d)?\b",
    "de": r"\b(du|dich|dir|dein\w*)\b",
    "es": r"\b(tú|tu|tus|ti|te|contigo|tuyo\w*|tuya\w*)\b",
}

# Spanish that is NOT neutral between Spain and Mexico (rule 1.4)
SPANISH_NON_NEUTRAL = (
    r"\b(vosotros|vosotras|vuestr\w+|coger|ordenador|móvil|vale|guay|chulo|mola|"
    r"chido|chévere|órale|ahorita|güey|padre|platicar|carro)\b"
)

# Hashtag language heuristics (rule 4.3). Tags that clearly belong to English.
ENGLISH_HASHTAGS = {
    "#homevibes", "#slowliving", "#cosyhome", "#cozyhome", "#kitchenlove", "#livingroom",
    "#wellbeing", "#homefragrance", "#homedecor", "#interiordesign", "#selfcare",
    "#homesweethome", "#mindfulliving", "#yogalife", "#candlelover", "#cosyvibes",
}

# Suggested local hashtags, shown to the LLM as examples.
LOCAL_HASHTAG_EXAMPLES = {
    "en": ["#SlowLiving", "#CosyHome", "#HomeVibes"],
    "de": ["#Wohnideen", "#Zuhause", "#Gemütlich"],
    "es": ["#HogarAcogedor", "#Decoración", "#Bienestar"],
}
CATEGORY_HASHTAGS = {
    "Kitchen": {"en": "#KitchenLove", "de": "#Küchenliebe", "es": "#Cocina"},
    "Living room": {"en": "#LivingRoom", "de": "#Wohnzimmer", "es": "#Salón"},
    "Wellbeing": {"en": "#Wellbeing", "de": "#Wohlbefinden", "es": "#Bienestar"},
    "Home fragrance": {"en": "#HomeFragrance", "de": "#Raumduft", "es": "#Aromas"},
}

# --------------------------------------------------------------------------
# Offline mock copy (used only by MockProvider: tests / demo without an API key).
# {name} is replaced by the exact product name.
# --------------------------------------------------------------------------
MOCK_CTA = {
    "en": "Tap the link in bio to see more.",
    "de": "Tippe auf den Link in der Bio und entdecke mehr.",
    "es": "Toca el enlace en la bio para ver más.",
}

MOCK_COPY: dict[tuple[str, str], tuple[str, str]] = {
    ("LL-001", "en"): (
        "Slow mornings start with a warm cup in your hands. Pour something you love and let the day wait. 🌿",
        "Your {name} has a hand-glazed finish that feels lovely to hold. It is dishwasher safe, so cleaning up stays easy.",
    ),
    ("LL-001", "de"): (
        "Langsame Morgen beginnen mit einer warmen Tasse in deinen Händen. Gieß dir etwas ein, das du liebst, und lass den Tag noch kurz warten. 🌿",
        "{name} überzeugt mit einer handglasierten Oberfläche. Außerdem ist es spülmaschinenfest, das Aufräumen bleibt einfach.",
    ),
    ("LL-001", "es"): (
        "Las mañanas lentas empiezan con una taza caliente entre tus manos. Sírvete algo que te guste y deja que el día espere. 🌿",
        "{name} tiene un acabado esmaltado a mano que se siente bien al sostenerlo. Además, es apto para lavavajillas y limpiar es fácil.",
    ),
    ("LL-002", "en"): (
        "Your evening deserves a soft place to land. Sink into the sofa and let the room go quiet. 🌿",
        "{name} is made from stonewashed linen. It gets softer with every wash, so it feels more like yours over time.",
    ),
    ("LL-002", "de"): (
        "Dein Abend verdient einen weichen Platz zum Ankommen. Sink ins Sofa und lass den Raum ganz ruhig werden. 🌿",
        "{name} besteht aus Stonewashed-Leinen. Mit jeder Wäsche wird es weicher und fühlt sich mit der Zeit mehr nach dir an.",
    ),
    ("LL-002", "es"): (
        "Tu tarde merece un rincón suave donde aterrizar. Húndete en el sofá y deja que la sala se quede en calma. 🌿",
        "{name} está hecho de lino lavado a la piedra. Se vuelve más suave con cada lavado y, con el tiempo, se siente más tuyo.",
    ),
    ("LL-003", "en"): (
        "Turn the lights low and let your evening slow down. A little warmth goes a long way. 🌿",
        "{name} runs for up to 8 hours on one fill. Its warm ambient light gives the room a soft glow.",
    ),
    ("LL-003", "de"): (
        "Dimm das Licht und lass deinen Abend langsamer werden. Ein bisschen Wärme reicht oft schon. 🌿",
        "{name} läuft bis zu 8 Stunden am Stück. Das warme Ambientelicht gibt deinem Raum einen sanften Schein.",
    ),
    ("LL-003", "es"): (
        "Baja las luces y deja que tu tarde vaya más despacio. Un poco de calidez hace mucho. 🌿",
        "{name} funciona hasta 8 horas seguidas. Su luz ambiental cálida le da a tu espacio un brillo suave.",
    ),
    ("LL-004", "en"): (
        "Roll out your mat and give yourself a few quiet minutes. No rush, just you and the floor. 🌿",
        "{name} has a natural cork surface you will enjoy under your hands. It stays grippy when wet, so you can keep your focus.",
    ),
    ("LL-004", "de"): (
        "Roll deine Matte aus und schenk dir ein paar ruhige Minuten. Kein Stress, nur du und der Boden. 🌿",
        "{name} hat eine Oberfläche aus Naturkork, die sich angenehm anfühlt. Sie bleibt auch bei Nässe rutschfest, so bleibst du konzentriert.",
    ),
    ("LL-004", "es"): (
        "Extiende tu esterilla y regálate unos minutos de calma. Sin prisa, solo tú y el suelo. 🌿",
        "{name} tiene una superficie de corcho natural muy agradable al tacto. Ofrece buen agarre incluso en mojado, para que mantengas tu enfoque.",
    ),
    ("LL-005", "en"): (
        "Light a candle and let the room feel like yours again. Evenings are allowed to be slow. 🌿",
        "{name} is made with soy wax. It burns for about 45 hours, so it stays with you for many evenings.",
    ),
    ("LL-005", "de"): (
        "Zünde eine Kerze an und lass den Raum wieder nach dir anfühlen. Abende dürfen langsam sein. 🌿",
        "{name} wird aus Sojawachs gefertigt. Sie brennt etwa 45 Stunden und begleitet dich durch viele Abende.",
    ),
    ("LL-005", "es"): (
        "Enciende una vela y deja que la habitación vuelva a sentirse tuya. Las tardes pueden ser lentas. 🌿",
        "{name} está hecha con cera de soja. Dura unas 45 horas y te acompaña durante muchas tardes.",
    ),
}
