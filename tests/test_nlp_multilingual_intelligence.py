"""SpaceLoop NLP & Full Multilingual Intelligence Test Suite
Validates the complete 6-language system:
  1. English (en)
  2. Hindi (hi)
  3. Marathi (mr)
  4. Garhwali (gsw)
  5. Kumaoni (kfy)
  6. Jaunsari (jns)
"""

from datetime import datetime, date, timedelta
import tempfile
import pytest

from app import create_app
from backend.core.database import db, init_db
from config import TestingConfig
from models import Space, User
from security import hash_password

from backend.modules.i18n.constants import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_NAMES,
    NATIVE_LANGUAGE_NAMES,
    normalize_language_code,
)
from backend.modules.i18n.detector import LanguageDetector
from backend.modules.i18n.lexicon import (
    localize_error,
    localize_space_type,
    localize_amenity,
    get_deterministic_response,
    MATCH_EXPLANATION_TEMPLATES,
)
from backend.modules.i18n.agreement_i18n import generate_multilingual_micro_lease
from backend.space_ai import get_oti_breakdown
from backend.modules.nlp.parser import QueryParser


def test_six_language_foundations():
    """Verify all 6 languages are distinctly registered with unique identities."""
    expected_langs = {"en", "hi", "mr", "gsw", "kfy", "jns"}
    assert set(SUPPORTED_LANGUAGES) == expected_langs
    assert len(SUPPORTED_LANGUAGES) == 6

    # Verify normalizer handles aliases, ISO variations and casing
    assert normalize_language_code("en-US") == "en"
    assert normalize_language_code("HI_in") == "hi"
    assert normalize_language_code("mr-IN") == "mr"
    assert normalize_language_code("gsw") == "gsw"
    assert normalize_language_code("kfy") == "kfy"
    assert normalize_language_code("jns") == "jns"
    assert normalize_language_code("garhwali") == "gsw"
    assert normalize_language_code("kumaoni") == "kfy"
    assert normalize_language_code("jaunsari") == "jns"
    assert normalize_language_code("unknown_xyz") == "en"

    # Distinct native names
    for lang in expected_langs:
        assert lang in LANGUAGE_NAMES
        assert lang in NATIVE_LANGUAGE_NAMES
        assert len(NATIVE_LANGUAGE_NAMES[lang]) > 0


def test_language_detection_distinct_pahari_and_regional():
    """Verify authentic language detection distinguishing Garhwali, Kumaoni, Jaunsari, Marathi, Hindi, and English."""
    # 1. English
    assert LanguageDetector.detect("Quiet desk near Indiranagar for 2 hours under 500 rupees") == "en"

    # 2. Hindi
    assert LanguageDetector.detect("कल दोपहर मुझे शांत कमरा चाहिए ५०० रुपये के अंदर") == "hi"

    # 3. Marathi
    assert LanguageDetector.detect("उद्या दुपारी शांत जागा हवी आहे ५०० रुपयांच्या आत") == "mr"

    # 4. Garhwali (contains authentic markers like 'भोल', 'छ', 'निछ', 'ठौर')
    assert LanguageDetector.detect("भोल सबेर शांत ठौर चयेंदू ५०० रुप्या मा, कूडू-कचरा निछ") == "gsw"

    # 5. Kumaoni (contains authentic markers like 'कैल', 'छु', 'न्है', 'ठौर')
    assert LanguageDetector.detect("कैल दुपहर शांत ठौर चैं ५०० रुपिया भितर, विवाद न्है") == "kfy"

    # 6. Jaunsari (contains authentic markers like 'नाइ', 'ओखत', 'जगा')
    assert LanguageDetector.detect("काल ओखत म शांत जगा चयी ५०० रुप्या भितर, कोई झमेला नाइ") == "jns"


def test_cross_language_nlp_parser_equivalence():
    """Verify cross-language extraction equivalence:
    Same intent in English, Hindi, Marathi, Garhwali, Kumaoni, Jaunsari produces equivalent parsed entities.
    """
    tomorrow_date = (date.today() + timedelta(days=1)).isoformat()

    queries = {
        "en": "Find a quiet desk tomorrow under 500",
        "hi": "कल शांत डेस्क चाहिए ५०० के अंदर",
        "mr": "उद्या शांत डेस्क हवी ५०० च्या आत",
        "gsw": "भोल शांत डेस्क चयेंदू ५०० मा",
        "kfy": "कैल शांत डेस्क चैं ५०० भितर",
        "jns": "काल शांत डेस्क चयी ५०० भितर",
    }

    for lang, text in queries.items():
        parsed = QueryParser.parse_query(text)
        # All 6 should detect budget
        assert parsed.get("budget") == 500.0, f"Budget value mismatch in {lang}: got {parsed.get('budget')}"

        # All 6 should detect noise preference
        assert parsed.get("noise_preference") == "quiet", f"Failed noise_preference in {lang}"

        # All 6 should detect tomorrow date
        assert parsed.get("date") == tomorrow_date, f"Failed date in {lang}: got {parsed.get('date')}, expected {tomorrow_date}"


def test_section_52_micro_lease_all_languages():
    """Verify statutory Section 52 Temporary Micro-Lease generation in all 6 supported languages."""
    space = {
        "id": "SP-101",
        "title": "Koramangala Quiet Pod",
        "address": "80 Feet Rd, 4th Block, Koramangala, Bengaluru",
        "host_name": "Rajesh Sharma",
    }
    booking = {
        "id": "BK-202",
        "guest_name": "Priya Patel",
        "start_iso": "2026-10-10 10:00",
        "end_iso": "2026-10-10 14:00",
        "duration_hours": 4,
        "amount": 400.0,
        "deposit_held": 100.0,
        "intended_purpose": "Study and Remote Work",
        "attendees": 1,
    }

    # Verify each language produces legally complete document
    for lang in SUPPORTED_LANGUAGES:
        lease = generate_multilingual_micro_lease(space, booking, language=lang)
        assert len(lease) > 200
        assert "BK-202" in lease
        assert "₹400" in lease or "400" in lease
        assert "₹100" in lease or "100" in lease

        # Verify language-specific legal title or header
        if lang == "en":
            assert "Section 52 of the Indian Easements Act, 1882" in lease
            assert "Parties & Premises" in lease
        elif lang == "hi":
            assert "भारतीय सुखाचार अधिनियम 1882 की धारा 52" in lease
            assert "पक्षकार एवं परिसर" in lease
        elif lang == "mr":
            assert "भारतीय सुखाधिकार कायदा 1882 च्या कलम 52" in lease
            assert "जागा" in lease
        elif lang == "gsw":
            assert "भारतीय सुखाचार अधिनियम 1882 की धारा 52" in lease
            assert "ठौर" in lease
        elif lang == "kfy":
            assert "भारतीय सुखाचार अधिनियम 1882 की धारा 52" in lease
            assert "जागा" in lease or "बखत" in lease
        elif lang == "jns":
            assert "भारतीय सुखाचार अधिनियम 1882 की धारा 52" in lease
            assert "ओखत" in lease or "ठौर" in lease


def test_oti_breakdown_all_languages():
    """Verify Objective Trust Index (OTI) breakdown produces localized explanations across all 6 languages."""
    for lang in SUPPORTED_LANGUAGES:
        breakdown = get_oti_breakdown(
            punctuality=95.0,
            condition_match=98.0,
            is_identity_verified=True,
            dispute_count=0,
            language=lang,
        )
        assert breakdown["total_score"] > 90.0
        assert breakdown["language"] == lang
        assert "punctuality" in breakdown
        assert "cleanliness" in breakdown
        assert "identity_trust" in breakdown
        assert "dispute_history" in breakdown
        assert len(breakdown["punctuality"]["description"]) > 10
        assert len(breakdown["cleanliness"]["description"]) > 10


def test_loopbot_deterministic_knowledge_all_languages():
    """Verify deterministic fallback responses for core platform concepts in all 6 languages."""
    intents = ["SECTION_52", "ESCROW", "CANCELLATION", "ARRIVAL_PIN", "GENERAL"]
    for lang in SUPPORTED_LANGUAGES:
        for intent in intents:
            resp = get_deterministic_response(intent, lang)
            assert resp is not None
            assert len(resp) > 30, f"Response too short for {intent} in {lang}"


def test_search_pipeline_localized_grounding():
    """Verify search templates and amenities provide localized match reasons across all 6 languages."""
    for lang in SUPPORTED_LANGUAGES:
        # Check rate explanation template
        rate_tpl = MATCH_EXPLANATION_TEMPLATES["rate_only"].get(lang)
        assert rate_tpl is not None, f"Missing rate template for {lang}"
        rendered_rate = rate_tpl.format(rate=200)
        assert "200" in rendered_rate

        # Check quiet environment explanation template
        quiet_tpl = MATCH_EXPLANATION_TEMPLATES["quiet_environment"].get(lang)
        assert quiet_tpl is not None, f"Missing quiet template for {lang}"
        assert len(quiet_tpl) > 5

        # Check localized amenities
        am = localize_amenity("wifi", lang)
        assert len(am) > 0
        desk = localize_space_type("desk", lang)
        assert len(desk) > 0


def test_error_localization_all_languages():
    """Verify API error messages are localized for all 6 languages."""
    error_codes = ["BAD_REQUEST", "UNAUTHORIZED", "FORBIDDEN", "NOT_FOUND", "RATE_LIMIT_EXCEEDED"]
    for lang in SUPPORTED_LANGUAGES:
        for code in error_codes:
            msg = localize_error(code, lang)
            assert msg is not None
            assert len(msg) > 5
            # Non-English should not be identical to English
            if lang != "en":
                assert msg != localize_error(code, "en")


def test_http_api_language_propagation_and_errors():
    """Verify end-to-end API header propagation and localized responses."""
    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")

    class TestCfg(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{temp_path}"
        SECRET_KEY = "test-secret-i18n-key"

    app = create_app(TestCfg)
    client = app.test_client()

    with app.app_context():
        init_db(app)

        # 1. Test 401 Unauthorized with X-Language: mr
        res_mr = client.get("/api/v1/auth/me", headers={"X-Language": "mr"})
        assert res_mr.status_code == 401
        data_mr = res_mr.get_json()
        assert data_mr["error"]["code"] == "UNAUTHORIZED"
        assert data_mr["error"]["language"] == "mr"
        assert data_mr["error"]["message"] == localize_error("UNAUTHORIZED", "mr")

        # 2. Test 401 Unauthorized with X-Language: gsw (Garhwali)
        res_gsw = client.get("/api/v1/auth/me", headers={"X-Language": "gsw"})
        assert res_gsw.status_code == 401
        data_gsw = res_gsw.get_json()
        assert data_gsw["error"]["code"] == "UNAUTHORIZED"
        assert data_gsw["error"]["language"] == "gsw"
        assert data_gsw["error"]["message"] == localize_error("UNAUTHORIZED", "gsw")

        # 3. Test 404 Not Found with X-Language: kfy (Kumaoni)
        res_kfy = client.get("/api/nonexistent-route", headers={"X-Language": "kfy"})
        assert res_kfy.status_code == 404
        data_kfy = res_kfy.get_json()
        assert data_kfy["error"]["language"] == "kfy"
        assert data_kfy["error"]["message"] == localize_error("NOT_FOUND", "kfy")
