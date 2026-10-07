"""Multilingual NLP parser and entity extraction engine for SpaceLoop.

Supports English, Hindi, Hinglish, and Marathi queries.
Extracts structured constraints: location, date, time, duration, budget, capacity, space_type, amenities, use_case.
"""

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.modules.nlp.lexicons import (
    AMENITY_SYNONYMS,
    CITY_ALIASES,
    CITY_CENTROIDS,
    NEIGHBORHOOD_MAP,
    NUMBER_WORDS,
    SPACE_TYPE_SYNONYMS,
    USE_CASE_SYNONYMS,
)


class QueryParser:
    """Deterministic multilingual natural language query parser for physical space search."""

    @classmethod
    def parse_query(cls, query: str | None) -> dict[str, Any]:
        """Parse raw query string into normalized structured discovery constraints."""
        if not query:
            return cls._empty_constraints()

        normalized = cls.normalize_text(query)

        # 1. Extract location (neighborhood, city, coordinates)
        loc_data = cls.extract_location(normalized)

        # 2. Extract date
        extracted_date = cls.extract_date(normalized)

        # 3. Extract time
        extracted_time = cls.extract_time(normalized)

        # 4. Extract duration in hours
        duration_hours = cls.extract_duration(normalized)

        # 5. Extract budget
        budget = cls.extract_budget(normalized)

        # 6. Extract capacity (guarded against duration collisions)
        capacity = cls.extract_capacity(normalized)

        # 7. Extract space type
        space_type = cls.extract_space_type(normalized)

        # 8. Extract amenities
        amenities = cls.extract_amenities(normalized)

        # 9. Extract use case
        use_case = cls.extract_use_case(normalized)

        return {
            "raw_query": query,
            "normalized_query": normalized,
            "city": loc_data.get("city"),
            "neighborhood": loc_data.get("neighborhood"),
            "latitude": loc_data.get("lat"),
            "longitude": loc_data.get("lng"),
            "date": extracted_date,
            "time": extracted_time,
            "duration_hours": duration_hours,
            "budget": budget,
            "capacity": capacity,
            "space_type": space_type,
            "amenities": amenities,
            "use_case": use_case,
        }

    @staticmethod
    def _empty_constraints() -> dict[str, Any]:
        return {
            "raw_query": "",
            "normalized_query": "",
            "city": None,
            "neighborhood": None,
            "latitude": None,
            "longitude": None,
            "date": None,
            "time": None,
            "duration_hours": None,
            "budget": None,
            "capacity": None,
            "space_type": None,
            "amenities": [],
            "use_case": None,
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode, strip redundant whitespace, convert to lowercase while preserving Devanagari."""
        nfkd = unicodedata.normalize("NFKD", text)
        cleaned = re.sub(r"[\t\r\n]+", " ", nfkd)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    @classmethod
    def extract_location(cls, text: str) -> dict[str, Any]:
        """Extract city, neighborhood, and geographical coordinates from multilingual query."""
        result: dict[str, Any] = {"city": None, "neighborhood": None, "lat": None, "lng": None}

        # Check neighborhoods first (more specific)
        for nh_key, nh_info in NEIGHBORHOOD_MAP.items():
            for alias in nh_info["aliases"]:
                pattern = rf"(?:\b|\s|^){re.escape(alias.lower())}(?:\b|\s|$|[,\.\?!])"
                if re.search(pattern, text):
                    result["neighborhood"] = nh_info["name"]
                    result["city"] = nh_info["city"]
                    result["lat"] = nh_info["lat"]
                    result["lng"] = nh_info["lng"]
                    return result

        # Check cities
        for alias, standard_city in CITY_ALIASES.items():
            pattern = rf"(?:\b|\s|^){re.escape(alias.lower())}(?:\b|\s|$|[,\.\?!])"
            if re.search(pattern, text):
                result["city"] = standard_city
                centroid = CITY_CENTROIDS.get(standard_city)
                if centroid:
                    result["lat"], result["lng"] = centroid
                return result

        return result

    @classmethod
    def extract_date(cls, text: str) -> str | None:
        """Extract booking date from relative or absolute date expressions."""
        now_utc = datetime.now(timezone.utc).date()

        # Absolute ISO date YYYY-MM-DD
        iso_match = re.search(r"\b(202\d-[01]\d-[0-3]\d)\b", text)
        if iso_match:
            return iso_match.group(1)

        # DD/MM/YYYY or DD-MM-YYYY
        dmy_match = re.search(r"\b([0-3]?\d)[/-]([01]?\d)[/-](202\d)\b", text)
        if dmy_match:
            d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
            try:
                return f"{y:04d}-{m:02d}-{d:02d}"
            except ValueError:
                pass

        # Relative days (English, Hindi, Hinglish, Marathi)
        # Day after tomorrow: "parso", "parwa", "day after tomorrow"
        if re.search(r"(?:\b|\s|^)(day after tomorrow|parso|parson|परसों|parwa|परवा)(?:\b|\s|$|[,\.\?!])", text):
            return (now_utc + timedelta(days=2)).isoformat()

        # Tomorrow: "tomorrow", "kal", "udya", "उद्या", "कल"
        if re.search(r"(?:\b|\s|^)(tomorrow|udya|उद्या|kal|कल)(?:\b|\s|$|[,\.\?!])", text):
            return (now_utc + timedelta(days=1)).isoformat()

        # Today: "today", "aaj", "आज", "aajcha diwas", "आजचा दिवस"
        if re.search(r"(?:\b|\s|^)(today|aaj|आज|aajcha diwas|आजचा दिवस)(?:\b|\s|$|[,\.\?!])", text):
            return now_utc.isoformat()

        # Next week: "next week", "agle hafte", "pudhchya aathvadyat"
        if re.search(r"(?:\b|\s|^)(next week|agle hafte|pudhchya aathvadyat|पुढच्या आठवड्यात)(?:\b|\s|$|[,\.\?!])", text):
            return (now_utc + timedelta(days=7)).isoformat()

        return None

    @classmethod
    def extract_time(cls, text: str) -> str | None:
        """Extract requested time of day or clock time (HH:MM)."""
        # Exact clock time with AM/PM: e.g. "10:30 am", "2pm", "4 pm"
        clock_match = re.search(r"\b([0-1]?\d)(?::([0-5]\d))?\s*(am|pm)\b", text)
        if clock_match:
            hour = int(clock_match.group(1))
            minute = int(clock_match.group(2) or 0)
            ampm = clock_match.group(3).lower()
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"

        # Hindi/Marathi baje/vajta: e.g. "4 baje", "11 vajta", "४ वाजता"
        baje_match = re.search(r"(?:\b|\s|^)(\d{1,2})\s*(?:baje|vajta|वाजता|वा)(?:\b|\s|$|[,\.\?!])", text)
        if baje_match:
            hour = int(baje_match.group(1))
            if 1 <= hour <= 7:
                hour += 12
            return f"{hour:02d}:00"

        # Broad time-of-day buckets
        if re.search(r"(?:\b|\s|^)(morning|subah|saver|सकाळी|sakaal|सकाळ)(?:\b|\s|$|[,\.\?!])", text):
            return "09:00"
        if re.search(r"(?:\b|\s|^)(afternoon|dopahar|dupahar|दुपारी|dupari)(?:\b|\s|$|[,\.\?!])", text):
            return "14:00"
        if re.search(r"(?:\b|\s|^)(evening|shaam|sandhya|संध्याकाळी|sandhyakali)(?:\b|\s|$|[,\.\?!])", text):
            return "17:00"
        if re.search(r"(?:\b|\s|^)(night|raat|रात्री|raatri)(?:\b|\s|$|[,\.\?!])", text):
            return "20:00"

        return None

    @classmethod
    def extract_duration(cls, text: str) -> float | None:
        """Extract booking duration in hours."""
        # Full day phrases: 8.0 hours
        if re.search(r"(?:\b|\s|^)(full day|poora din|ek din|purna divas|ek divas|पूर्ण दिवस|एक दिवस)(?:\b|\s|$|[,\.\?!])", text):
            return 8.0

        # Half day phrases: 4.0 hours
        if re.search(r"(?:\b|\s|^)(half day|aadha din|ardha divas|अर्धा दिवस)(?:\b|\s|$|[,\.\?!])", text):
            return 4.0

        # Numeric duration: e.g. "2 hours", "3.5 hrs", "4 ghante", "3 taas", "३ तास"
        num_match = re.search(
            r"(?:\b|\s|^)(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|ghante|ghanta|घंटे|taas|tas|तास|तासांसाठी)(?:\b|\s|$|[,\.\?!])",
            text,
        )
        if num_match:
            return float(num_match.group(1))

        # Word duration: e.g. "do ghante", "teen taas", "four hours"
        for word, val in NUMBER_WORDS.items():
            pattern = rf"(?:\b|\s|^){re.escape(word)}\s*(?:hours|hrs|ghante|ghanta|taas|tas|तास)(?:\b|\s|$|[,\.\?!])"
            if re.search(pattern, text):
                return float(val)

        return None

    @classmethod
    def extract_budget(cls, text: str) -> float | None:
        """Extract maximum price/budget constraint in INR."""
        # Check patterns with currency units or budget boundaries
        patterns = [
            # "under 500", "below 1000", "budget 1500", "max 2000", "₹800", "rs 800"
            r"(?:under|below|budget|max|upto|up to|₹|rs\.?|inr|कमी)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|hazar|hazaar|thousand|हजार)?(?:\b|\s|$|[,\.\?!])",
            # "500 rs", "1000 rupees", "300 रुपयांच्या आत", "500 रुपये"
            r"(?:\b|\s|^)(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|hazar|hazaar|thousand|हजार)?\s*(?:rs|inr|rupees|rupaye|rupay|rupayan|रुपये|रुपयांच्या|रुपयांचे|रु)\s*(?:chya aat|chya aath|paryant|ke andar|tak|च्या आत|आत|पर्यंत)?(?:\b|\s|$|[,\.\?!])",
            # "300 च्या आत", "500 तक"
            r"(?:\b|\s|^)(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:chya aat|chya aath|paryant|ke andar|tak|च्या आत|आत|पर्यंत)(?:\b|\s|$|[,\.\?!])",
        ]

        for pat in patterns:
            match = re.search(pat, text)
            if match:
                raw_num = match.group(1).replace(",", "")
                val = float(raw_num)
                # Check multiplier
                if len(match.groups()) > 1 and match.group(2):
                    mult = match.group(2).lower()
                    if mult in ("k", "hazar", "hazaar", "thousand", "हजार"):
                        val *= 1000.0
                return val

        # Check cheap/budget cues (no explicit number given, set sensible cap of 300/hr)
        if re.search(r"(?:\b|\s|^)(sasta|kam budget|sasti|kam daam|kami kharchat|cheap|budget friendly|low cost|किफायतशीर)(?:\b|\s|$|[,\.\?!])", text):
            return 300.0

        return None

    @classmethod
    def extract_capacity(cls, text: str) -> int | None:
        """Extract minimum seating capacity, avoiding duration collisions."""
        # Solo / single cues
        if re.search(r"(?:\b|\s|^)(solo|single person|akela|ek vyakti|ekach vyakti|एकटा|एक व्यक्ती)(?:\b|\s|$|[,\.\?!])", text):
            return 1

        # "team of 10", "group of 6", "seats 6"
        p1 = re.search(r"(?:team of|group of|seats)\s*(\d+)", text)
        if p1:
            return int(p1.group(1))

        # "for 4 people", "for 6 persons", "6 logo ke liye", "5 लोकांसाठी"
        p2 = re.search(
            r"(?:\b|\s|^)(?:for\s+)?(\d+)\s*(?:people|persons|members|pax|seats|log|logo|vyakti|jan|lok|लोग|लोकांसाठी|लोक|व्यक्ती|जण)(?:\b|\s|$|[,\.\?!])",
            text,
        )
        if p2:
            return int(p2.group(1))

        # Word numbers: "char log", "panch vyakti", "don jan", "team of six"
        for word, val in NUMBER_WORDS.items():
            pattern = rf"(?:\b|\s|^)(?:team of|for\s+)?{re.escape(word)}\s*(?:people|persons|members|pax|seats|log|logo|lok|vyakti|jan|लोग|लोक|व्यक्ती)(?:\b|\s|$|[,\.\?!])"
            if re.search(pattern, text):
                return val

        return None

    @classmethod
    def extract_space_type(cls, text: str) -> str | None:
        """Extract requested typology (desk, room, meeting_room, studio, commercial, creative)."""
        for st_key, synonyms in SPACE_TYPE_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"(?:\b|\s|^){re.escape(syn.lower())}(?:\b|\s|$|[,\.\?!])"
                if re.search(pattern, text):
                    return st_key
        return None

    @classmethod
    def extract_amenities(cls, text: str) -> list[str]:
        """Extract list of requested amenities."""
        extracted = []
        for amenity_key, synonyms in AMENITY_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"(?:\b|\s|^){re.escape(syn.lower())}(?:\b|\s|$|[,\.\?!])"
                if re.search(pattern, text):
                    if amenity_key not in extracted:
                        extracted.append(amenity_key)
                    break
        return extracted

    @classmethod
    def extract_use_case(cls, text: str) -> str | None:
        """Extract intended activity/use case."""
        for uc_key, synonyms in USE_CASE_SYNONYMS.items():
            for syn in synonyms:
                pattern = rf"(?:\b|\s|^){re.escape(syn.lower())}(?:\b|\s|$|[,\.\?!])"
                if re.search(pattern, text):
                    return uc_key
        return None
