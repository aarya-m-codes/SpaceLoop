"""SpaceLoop Multilingual Subsystem Package."""

from backend.modules.i18n.agreement_i18n import generate_multilingual_micro_lease
from backend.modules.i18n.constants import (
    DEFAULT_LANGUAGE,
    LANG_EN,
    LANG_GSW,
    LANG_HI,
    LANG_HINGLISH,
    LANG_JNS,
    LANG_KFY,
    LANG_MR,
    LANGUAGE_METADATA,
    SUPPORTED_LANGUAGES,
    normalize_language_code,
)
from backend.modules.i18n.detector import LanguageDetector, detect_language
from backend.modules.i18n.lexicon import (
    AMENITIES,
    ERROR_MESSAGES,
    MATCH_EXPLANATION_TEMPLATES,
    SPACE_TYPES,
    get_deterministic_response,
    localize_amenity,
    localize_error,
    localize_space_type,
)
from backend.modules.i18n.middleware import get_request_language, localized_json_error

__all__ = [
    "LANG_EN",
    "LANG_HI",
    "LANG_MR",
    "LANG_GSW",
    "LANG_KFY",
    "LANG_JNS",
    "LANG_HINGLISH",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
    "LANGUAGE_METADATA",
    "normalize_language_code",
    "LanguageDetector",
    "detect_language",
    "ERROR_MESSAGES",
    "SPACE_TYPES",
    "AMENITIES",
    "MATCH_EXPLANATION_TEMPLATES",
    "localize_error",
    "localize_space_type",
    "localize_amenity",
    "get_deterministic_response",
    "generate_multilingual_micro_lease",
    "get_request_language",
    "localized_json_error",
]
