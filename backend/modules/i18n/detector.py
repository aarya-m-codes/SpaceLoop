"""Language detection engine for SpaceLoop.

Accurately distinguishes among the six supported languages:
- English (en)
- Hindi (hi)
- Marathi (mr)
- Garhwali (gsw)
- Kumaoni (kfy)
- Jaunsari (jns)
Plus handles Romanized queries (Hinglish, Romanized Marathi/Pahari).
"""

import re
import unicodedata
from backend.modules.i18n.constants import (
    DEFAULT_LANGUAGE,
    LANG_EN,
    LANG_GSW,
    LANG_HI,
    LANG_HINGLISH,
    LANG_JNS,
    LANG_KFY,
    LANG_MR,
)


class LanguageDetector:
    """Robust multilingual classifier for SpaceLoop discovery, LoopBot, and messaging."""

    # -------------------------------------------------------------
    # 1. Garhwali (gsw) Lexical & Morphological Markers (Devanagari)
    # -------------------------------------------------------------
    GARHWALI_MARKERS: list[str] = [
        "ठौर", "खोली", "भोल", "ब्याली", "सबेर", "ब्याल", "सुभीता", "बगत",
        "रुप्या", "टका", "खोजणा", "खोजण", "पैलाग", "निछ", "दिय्यां", "अपणु",
        "अपणी", "कख", "कन", "कथगा", "किले", "किकिले", "हमरो", "हमरी", "छन",
        "छा", "ह्वै", "ह्वेल", "ह्वोला", "ह्वोली", "छे", "निछा",
    ]

    # Regex patterns for Garhwali copula & verbal forms (word boundary matching)
    GARHWALI_PATTERNS: list[str] = [
        r"(?:\b|\s|^)(?:छ|छा|छन|छे|निछ|ह्वै|ह्वेल)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:कख|कन|कथगा|किले|अपणु|अपणी)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:भोल|ब्याली|सबेर|ब्याल|सुभीता|ठौर)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:रुप्या|टका)(?:\b|\s|$|[,\.\?!])",
    ]

    # -------------------------------------------------------------
    # 2. Kumaoni (kfy) Lexical & Morphological Markers (Devanagari)
    # -------------------------------------------------------------
    KUMAONI_MARKERS: list[str] = [
        "ठौर", "कैल", "परों", "बखत", "घण्टा", "सुभीत", "ढूंण", "फिर्ता",
        "रुपिया", "सावचेत", "छु", "छौ", "छि", "छन", "न्है", "भै", "होल",
        "होला", "होली", "काँ", "काहाँ", "कबे", "कसो", "कसि", "केतुक", "कतुक",
        "तुमरो", "तुमर", "होलि", "कैल",
    ]

    KUMAONI_PATTERNS: list[str] = [
        r"(?:\b|\s|^)(?:छु|छौ|छि|न्है|भै|होल)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:काँ|काहाँ|कबे|कसो|कसि|केतुक|कतुक)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:कैल|परों|बखत|घण्टा|सुभीत|ढूंण)(?:\b|\s|$|[,\.\?!])",
    ]

    # -------------------------------------------------------------
    # 3. Jaunsari (jns) Lexical & Morphological Markers (Devanagari)
    # -------------------------------------------------------------
    JAUNSARI_MARKERS: list[str] = [
        "ठौर", "ओखत", "काल्ह", "आजि", "पिसे", "सुआणो", "सुभीतो", "हेरणा",
        "अमानत", "नाइ", "नाह", "होलो", "होलि", "होले", "आऊ", "माऊ", "हामे",
        "तुमे", "तुमारो", "कुई", "कुआ", "किसो", "किक", "केतरो", "घंटे",
    ]

    JAUNSARI_PATTERNS: list[str] = [
        r"(?:\b|\s|^)(?:नाइ|नाह|होलो|होलि|होले)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:आऊ|माऊ|हामे|तुमे|कुई|कुआ|किसो|केतरो)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:काल्ह|आजि|ओखत|पिसे|सुआणो|सुभीतो|हेरणा)(?:\b|\s|$|[,\.\?!])",
    ]

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # 4. Marathi (mr) Markers (Devanagari)
    # -------------------------------------------------------------
    MARATHI_MARKERS: list[str] = [
        "आहे", "नाही", "पाहिजे", "कसे", "मला", "शोधत", "शोधतो",
        "माहिती", "कसा", "करा", "नका", "होय", "किती",
        "झाले", "मिळेल", "पुणे", "मुंबई", "जागा", "कशी", "करावे",
        "थेट", "तक्रार", "तास", "उद्या", "परवा", "च्या आत", "साठी",
        "पर्यंत", "आहेत", "हवी", "हवा", "होते", "होती", "भाडेतत्त्वावर",
    ]

    MARATHI_PATTERNS: list[str] = [
        r"(?:\b|\s|^)(?:आहे|नाही|पाहिजे|हवी|हवा|आहेत|होते|होती)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:च्या आत|साठी|पर्यंत|कडून|मध्ये)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:मला|तुला|आम्हाला|त्यांना|आपणास)(?:\b|\s|$|[,\.\?!])",
    ]

    # -------------------------------------------------------------
    # 5. Hindi (hi) Markers (Devanagari)
    # -------------------------------------------------------------
    HINDI_MARKERS: list[str] = [
        "है", "हैं", "था", "थी", "थे", "चाहिए", "मुझे", "कमरा", "स्थान", "दोपहर",
        "कल", "परसों", "घंटे", "अंदर", "कहाँ", "कैसे", "किराया", "रुपये", "पैसा",
        "शांत", "कार्यालय", "नमस्ते", "सुविधाएं", "बुकिंग", "रद्द",
    ]

    HINDI_PATTERNS: list[str] = [
        r"(?:\b|\s|^)(?:है|हैं|था|थी|थे|होगी|होगा)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:चाहिए|मुझे|हमे|हमारा|तुम्हारा|आपका)(?:\b|\s|$|[,\.\?!])",
        r"(?:\b|\s|^)(?:के अंदर|के लिए|में|से|को|का|की|के)(?:\b|\s|$|[,\.\?!])",
    ]

    # -------------------------------------------------------------
    # 6. Romanized Patterns
    # -------------------------------------------------------------
    ROMAN_MARATHI_PATTERNS: list[str] = [
        r"\bahe\b", r"\bnahi\b", r"\bpahije\b", r"\bkashi\b", r"\bkiti\b",
        r"\bkuthe\b", r"\bmadhe\b", r"\bmala\b", r"\bsangava\b", r"\bmahiti\b",
        r"\bkaraychi\b", r"\bbhaden\b", r"\bkarave\b", r"\bshodh\b", r"\btakrar\b",
        r"\btaas\b", r"\budya\b",
    ]

    ROMAN_GARHWALI_PATTERNS: list[str] = [
        r"\bthaur\b", r"\bkholi\b", r"\bbhol\b", r"\bsubhita\b", r"\brupya\b",
        r"\bchha\b", r"\bnich\b", r"\bpailag\b", r"\bkakh\b", r"\bbhyali\b",
    ]

    ROMAN_KUMAONI_PATTERNS: list[str] = [
        r"\bkail\b", r"\bbakhat\b", r"\bsubhit\b", r"\bchhuko\b", r"\bketuk\b",
        r"\bfirta\b", r"\bkoso\b", r"\bkaahan\b",
    ]

    ROMAN_JAUNSARI_PATTERNS: list[str] = [
        r"\bsuano\b", r"\bsuan\b", r"\bokhat\b", r"\bkalh\b", r"\baaji\b",
        r"\bpise\b", r"\bherna\b", r"\bketro\b", r"\bholo\b",
    ]

    ROMAN_HINGLISH_PATTERNS: list[str] = [
        r"\bmujhe\b", r"\bchahiye\b", r"\bmein\b", r"\bkaise\b", r"\bhoga\b",
        r"\bkarna\b", r"\bhai\b", r"\bkya\b", r"\bsath\b", r"\bpaise\b",
        r"\bbatao\b", r"\bkarein\b", r"\bkitna\b", r"\bmilega\b", r"\bdekhna\b",
        r"\bbataiye\b", r"\bkaru\b", r"\braha\b", r"\brahi\b", r"\bhain\b",
        r"\bki\b", r"\bse\b", r"\bko\b", r"\baap\b", r"\bhum\b", r"\bkare\b",
        r"\bkaha\b", r"\bkab\b", r"\bkisko\b", r"\brupaye\b", r"\bkamra\b",
        r"\bdhoondo\b", r"\bkhojo\b", r"\bwapas\b", r"\bradd\b",
    ]

    @classmethod
    def detect(cls, text: str | None, allow_hinglish: bool = False) -> str:
        """Detect language from string input. Returns canonical code ('en', 'hi', 'mr', 'gsw', 'kfy', 'jns') or 'hinglish' if allowed."""
        if not text:
            return DEFAULT_LANGUAGE

        normalized = unicodedata.normalize("NFKD", str(text)).strip()
        if not normalized:
            return DEFAULT_LANGUAGE

        # -------------------------------------------------------------
        # Phase 1: Devanagari script detection (\u0900-\u097F)
        # -------------------------------------------------------------
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", normalized))

        if has_devanagari:
            # Check regional languages with distinct morphological scoring
            score_gsw = sum(1 for m in cls.GARHWALI_MARKERS if m in normalized)
            for pat in cls.GARHWALI_PATTERNS:
                if re.search(pat, normalized):
                    score_gsw += 2

            score_kfy = sum(1 for m in cls.KUMAONI_MARKERS if m in normalized)
            for pat in cls.KUMAONI_PATTERNS:
                if re.search(pat, normalized):
                    score_kfy += 2

            score_jns = sum(1 for m in cls.JAUNSARI_MARKERS if m in normalized)
            for pat in cls.JAUNSARI_PATTERNS:
                if re.search(pat, normalized):
                    score_jns += 2

            score_mr = sum(1 for m in cls.MARATHI_MARKERS if m in normalized)
            for pat in cls.MARATHI_PATTERNS:
                if re.search(pat, normalized):
                    score_mr += 2

            score_hi = sum(1 for m in cls.HINDI_MARKERS if m in normalized)
            for pat in cls.HINDI_PATTERNS:
                if re.search(pat, normalized):
                    score_hi += 2

            # Evaluate regional Pahari languages first if their specific markers trigger
            if score_jns > 0 and score_jns >= score_gsw and score_jns >= score_kfy and score_jns >= score_mr and score_jns >= score_hi:
                return LANG_JNS

            if score_gsw > 0 and score_gsw >= score_kfy and score_gsw >= score_mr and score_gsw >= score_hi:
                return LANG_GSW

            if score_kfy > 0 and score_kfy >= score_mr and score_kfy >= score_hi:
                return LANG_KFY

            if score_mr > 0 and score_mr > score_hi:
                return LANG_MR

            # Default or highest Devanagari match is Hindi
            return LANG_HI

        # -------------------------------------------------------------
        # Phase 2: Romanized / Latin script detection
        # -------------------------------------------------------------
        lower_text = normalized.lower()

        # Check Romanized Jaunsari
        for pat in cls.ROMAN_JAUNSARI_PATTERNS:
            if re.search(pat, lower_text):
                return LANG_JNS

        # Check Romanized Garhwali
        for pat in cls.ROMAN_GARHWALI_PATTERNS:
            if re.search(pat, lower_text):
                return LANG_GSW

        # Check Romanized Kumaoni
        for pat in cls.ROMAN_KUMAONI_PATTERNS:
            if re.search(pat, lower_text):
                return LANG_KFY

        # Check Romanized Marathi
        for pat in cls.ROMAN_MARATHI_PATTERNS:
            if re.search(pat, lower_text):
                return LANG_MR

        # Check Hinglish
        for pat in cls.ROMAN_HINGLISH_PATTERNS:
            if re.search(pat, lower_text):
                return LANG_HINGLISH if allow_hinglish else LANG_HI

        # Default to English for general Latin text
        return LANG_EN


def detect_language(text: str | None, allow_hinglish: bool = False) -> str:
    """Convenience helper for language detection."""
    return LanguageDetector.detect(text, allow_hinglish=allow_hinglish)
