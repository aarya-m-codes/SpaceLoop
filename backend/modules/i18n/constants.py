"""SpaceLoop Multilingual Subsystem Constants.

Defines the six canonical languages supported across the entire SpaceLoop platform:
1. English (en) - Global / National Lingua Franca
2. Hindi (hi) - National Language / Northern Metros
3. Marathi (mr) - Maharashtra (Mumbai, Pune)
4. Garhwali (gsw) - Central Pahari (Garhwal, Uttarakhand)
5. Kumaoni (kfy) - Central Pahari (Kumaon, Uttarakhand)
6. Jaunsari (jns) - Western Pahari (Jaunsar-Bawar, Uttarakhand)
"""

from typing import Any

# Canonical language identifiers
LANG_EN = "en"
LANG_HI = "hi"
LANG_MR = "mr"
LANG_GSW = "gsw"
LANG_KFY = "kfy"
LANG_JNS = "jns"
LANG_HINGLISH = "hinglish"  # Colloquial mixed mode, resolves primarily to Hindi with Romanized tolerance

SUPPORTED_LANGUAGES: list[str] = [
    LANG_EN,
    LANG_HI,
    LANG_MR,
    LANG_GSW,
    LANG_KFY,
    LANG_JNS,
]

DEFAULT_LANGUAGE: str = LANG_EN

LANGUAGE_METADATA: dict[str, dict[str, Any]] = {
    LANG_EN: {
        "code": LANG_EN,
        "label": "English",
        "native": "English",
        "flag": "🇬🇧",
        "script": "Latin",
        "family": "Indo-European (Germanic)",
        "region": "Global / Metros",
        "greeting": "Hello",
        "welcome": "Welcome to SpaceLoop",
    },
    LANG_HI: {
        "code": LANG_HI,
        "label": "Hindi",
        "native": "हिन्दी",
        "flag": "🇮🇳",
        "script": "Devanagari",
        "family": "Indo-Aryan (Central)",
        "region": "National / North India",
        "greeting": "नमस्ते",
        "welcome": "स्पेस-लूप में आपका स्वागत है",
    },
    LANG_MR: {
        "code": LANG_MR,
        "label": "Marathi",
        "native": "मराठी",
        "flag": "🇮🇳",
        "script": "Devanagari",
        "family": "Indo-Aryan (Southern)",
        "region": "Maharashtra (Mumbai, Pune)",
        "greeting": "नमस्कार",
        "welcome": "स्पेस-लूपमध्ये आपले स्वागत आहे",
    },
    LANG_GSW: {
        "code": LANG_GSW,
        "label": "Garhwali",
        "native": "गढ़वळि",
        "flag": "🏔️",
        "script": "Devanagari",
        "family": "Central Pahari",
        "region": "Garhwal, Uttarakhand",
        "greeting": "प्रणाम / पैलाग",
        "welcome": "स्पेस-लूप मा आपू को स्वागत छ",
    },
    LANG_KFY: {
        "code": LANG_KFY,
        "label": "Kumaoni",
        "native": "कुमाउँनी",
        "flag": "🌲",
        "script": "Devanagari",
        "family": "Central Pahari",
        "region": "Kumaon, Uttarakhand",
        "greeting": "पैलाग / नमस्कार",
        "welcome": "स्पेस-लूप भितर तुमरो स्वागत छु",
    },
    LANG_JNS: {
        "code": LANG_JNS,
        "label": "Jaunsari",
        "native": "जौनसारी",
        "flag": "⛰️",
        "script": "Devanagari",
        "family": "Western Pahari",
        "region": "Jaunsar-Bawar, Uttarakhand",
        "greeting": "नमस्ते / प्रणाम",
        "welcome": "स्पेस-लूप मा तुमारो सुआणो स्वागत आ",
    },
}

LANGUAGE_NAMES: dict[str, str] = {code: meta["label"] for code, meta in LANGUAGE_METADATA.items()}
NATIVE_LANGUAGE_NAMES: dict[str, str] = {code: meta["native"] for code, meta in LANGUAGE_METADATA.items()}



def normalize_language_code(code: str | None) -> str:
    """Normalize input language code string to one of the 6 canonical languages."""
    if not code:
        return DEFAULT_LANGUAGE
    clean = str(code).strip().lower().replace("_", "-")
    # Exact match
    if clean in SUPPORTED_LANGUAGES:
        return clean
    if clean == LANG_HINGLISH:
        return LANG_HI
    # Prefix matches e.g. en-US -> en, hi-IN -> hi, mr-IN -> mr
    prefix = clean.split("-")[0]
    if prefix in SUPPORTED_LANGUAGES:
        return prefix
    # Common aliases
    aliases = {
        "eng": LANG_EN,
        "hin": LANG_HI,
        "mar": LANG_MR,
        "garh": LANG_GSW,
        "garhwali": LANG_GSW,
        "kum": LANG_KFY,
        "kumaoni": LANG_KFY,
        "kumauni": LANG_KFY,
        "jaun": LANG_JNS,
        "jaunsari": LANG_JNS,
    }
    return aliases.get(clean, DEFAULT_LANGUAGE)
