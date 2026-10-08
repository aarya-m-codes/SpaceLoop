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


DEV_DIGIT_MAP = str.maketrans("०१२३४५६७८९", "0123456789")


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

        # 3. Extract time & time range
        range_start, range_end, range_dur = cls.extract_time_range(normalized)
        extracted_time = range_start or cls.extract_time(normalized)
        extracted_end_time = range_end

        # 4. Extract duration in hours
        duration_hours = range_dur or cls.extract_duration(normalized)

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

        # 10. Extract noise preference
        noise_pref = cls.extract_noise_preference(normalized)
        if noise_pref == "quiet" and "quiet" not in amenities:
            amenities.append("quiet")

        # 11. Extract privacy
        privacy = cls.extract_privacy(normalized)

        # 12. Extract landmark & radius
        landmark = cls.extract_landmark(normalized)
        radius = cls.extract_radius(normalized)
        is_near_me = bool(re.search(r"(?:\b|\s|^)(near me|nearby|around me|pas me|javal)(?:\b|\s|$|[,\.\?!])", normalized))

        # 13. Extract keywords
        keywords = cls.extract_keywords(normalized)

        # 14. Build semantic query
        semantic_query = cls.build_semantic_query(
            normalized=normalized,
            space_type=space_type,
            amenities=amenities,
            use_case=use_case,
            noise_pref=noise_pref,
            city=loc_data.get("city"),
        )

        location_display = loc_data.get("neighborhood") or loc_data.get("city")
        if landmark:
            location_display = f"{landmark} ({location_display})" if location_display else landmark

        return {
            "raw_query": query,
            "normalized_query": normalized,
            "intent": "search",
            "city": loc_data.get("city"),
            "neighborhood": loc_data.get("neighborhood"),
            "landmark": landmark,
            "is_near_me": is_near_me,
            "location": location_display,
            "latitude": loc_data.get("lat"),
            "longitude": loc_data.get("lng"),
            "radius": radius,
            "radius_km": radius,
            "date": extracted_date,
            "time": extracted_time,
            "start_time": extracted_time,
            "end_time": extracted_end_time,
            "duration": duration_hours,
            "duration_hours": duration_hours,
            "budget": budget,
            "capacity": capacity,
            "space_type": space_type,
            "amenities": amenities,
            "purpose": use_case,
            "use_case": use_case,
            "noise_preference": noise_pref,
            "privacy": privacy,
            "keywords": keywords,
            "semantic_query": semantic_query,
        }

    @staticmethod
    def _empty_constraints() -> dict[str, Any]:
        return {
            "raw_query": "",
            "normalized_query": "",
            "intent": "search",
            "city": None,
            "neighborhood": None,
            "landmark": None,
            "is_near_me": False,
            "location": None,
            "latitude": None,
            "longitude": None,
            "radius": None,
            "radius_km": None,
            "date": None,
            "time": None,
            "start_time": None,
            "end_time": None,
            "duration": None,
            "duration_hours": None,
            "budget": None,
            "capacity": None,
            "space_type": None,
            "amenities": [],
            "purpose": None,
            "use_case": None,
            "noise_preference": None,
            "privacy": None,
            "keywords": [],
            "semantic_query": "",
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode, strip redundant whitespace, convert Devanagari digits to ASCII, and lowercase."""
        nfkd = unicodedata.normalize("NFKD", text)
        cleaned = re.sub(r"[\t\r\n]+", " ", nfkd)
        cleaned = cleaned.translate(DEV_DIGIT_MAP)
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

        # Relative days across all 6 languages (English, Hindi, Marathi, Garhwali, Kumaoni, Jaunsari)
        # Day after tomorrow: "parso", "parwa", "day after tomorrow", "परसों", "परवा", "परों"
        if re.search(r"(?:\b|\s|^)(day after tomorrow|parso|parson|परसों|parwa|परवा|परों)(?:\b|\s|$|[,\.\?!])", text):
            return (now_utc + timedelta(days=2)).isoformat()

        # Tomorrow: "tomorrow", "kal", "udya", "उद्या", "kal", "कल", "काल", "भोल", "कैल", "काल्ह"
        if re.search(r"(?:\b|\s|^)(tomorrow|udya|उद्या|kal|कल|काल|भोल|कैल|काल्ह)(?:\b|\s|$|[,\.\?!])", text):
            return (now_utc + timedelta(days=1)).isoformat()

        # Today: "today", "aaj", "आज", "aajcha diwas", "आजचा दिवस", "आजि"
        if re.search(r"(?:\b|\s|^)(today|aaj|आज|aajcha diwas|आजचा दिवस|आजि)(?:\b|\s|$|[,\.\?!])", text):
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

        # Hindi/Marathi/Pahari baje/vajta/bakhata: e.g. "4 baje", "11 vajta", "४ वाजता", "३ बजे"
        baje_match = re.search(r"(?:\b|\s|^)(\d{1,2})\s*(?:baje|vajta|वाजता|वा|बजे|बगत|बखत|ओखत)(?:\b|\s|$|[,\.\?!])", text)
        if baje_match:
            hour = int(baje_match.group(1))
            if 1 <= hour <= 7:
                hour += 12
            return f"{hour:02d}:00"

        # Broad time-of-day buckets across all 6 languages
        # Morning: morning, subah, saver, सकाळी, सकाळ, सबेर, सबेरे
        if re.search(r"(?:\b|\s|^)(morning|subah|saver|सकाळी|sakaal|सकाळ|सबेर|सबेरे)(?:\b|\s|$|[,\.\?!])", text):
            return "09:00"
        # Afternoon: afternoon, dopahar, dupahar, दुपारी, दुपार
        if re.search(r"(?:\b|\s|^)(afternoon|dopahar|dupahar|दुपारी|dupari|दुपार)(?:\b|\s|$|[,\.\?!])", text):
            return "14:00"
        # Evening: evening, shaam, sandhya, संध्याकाळी, ब्याल, सांझ
        if re.search(r"(?:\b|\s|^)(evening|shaam|sandhya|संध्याकाळी|sandhyakali|ब्याल|सांझ)(?:\b|\s|$|[,\.\?!])", text):
            return "17:00"
        # Night: night, raat, रात्री, रात, ब्याली
        if re.search(r"(?:\b|\s|^)(night|raat|रात्री|raatri|रात)(?:\b|\s|$|[,\.\?!])", text):
            return "20:00"

        return None

    @classmethod
    def extract_duration(cls, text: str) -> float | None:
        """Extract booking duration in hours."""
        # Full day phrases: 8.0 hours
        if re.search(r"(?:\b|\s|^)(full day|poora din|ek din|purna divas|ek divas|पूर्ण दिवस|एक दिवस|पूरो दिन|पूर दिन)(?:\b|\s|$|[,\.\?!])", text):
            return 8.0

        # Half day phrases: 4.0 hours
        if re.search(r"(?:\b|\s|^)(half day|aadha din|ardha divas|अर्धा दिवस|आधो दिन)(?:\b|\s|$|[,\.\?!])", text):
            return 4.0

        # Numeric duration: e.g. "2 hours", "3.5 hrs", "4 ghante", "3 taas", "३ तास", "४ घंटा", "२ घण्टा"
        num_match = re.search(
            r"(?:\b|\s|^)(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|ghante|ghanta|घंटे|घंटा|घण्टा|taas|tas|तास|तासांसाठी)(?:\b|\s|$|[,\.\?!])",
            text,
        )
        if num_match:
            return float(num_match.group(1))

        # Word duration: e.g. "do ghante", "teen taas", "four hours", "दुई घंटा"
        for word, val in NUMBER_WORDS.items():
            pattern = rf"(?:\b|\s|^){re.escape(word)}\s*(?:hours|hrs|ghante|ghanta|घंटे|घंटा|घण्टा|taas|tas|तास)(?:\b|\s|$|[,\.\?!])"
            if re.search(pattern, text):
                return float(val)

        return None

    @classmethod
    def extract_budget(cls, text: str) -> float | None:
        """Extract maximum price/budget constraint in INR."""
        # Check patterns with currency units or budget boundaries
        patterns = [
            # "under 500", "below 1000", "budget 1500", "max 2000", "₹800", "rs 800", "कमी 500", "सस्त 400"
            r"(?:under|below|budget|max|upto|up to|₹|rs\.?|inr|कमी|सस्त|सुआणो)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|hazar|hazaar|thousand|हजार)?(?:\b|\s|$|[,\.\?!])",
            # "500 rs", "1000 rupees", "300 रुपयांच्या आत", "500 रुपये", "400 रुप्या मा", "500 रुपिया भितर", "300 पिसे"
            r"(?:\b|\s|^)(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|hazar|hazaar|thousand|हजार)?\s*(?:rs|inr|rupees|rupaye|rupay|rupayan|रुपये|रुपयांच्या|रुपयांचे|रु|रुप्या|टका|रुपिया|पिसे)\s*(?:chya aat|chya aath|paryant|ke andar|tak|च्या आत|आत|पर्यंत|तक|मा|भितर|अन्दर|अंदर|के अंदर|के अन्दर)?(?:\b|\s|$|[,\.\?!])",
            # "300 च्या आत", "500 तक", "400 मा", "500 भितर", "500 के अंदर", "500 अंदर"
            r"(?:\b|\s|^)(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:chya aat|chya aath|paryant|ke andar|tak|च्या आत|आत|पर्यंत|तक|मा|भितर|अन्दर|अंदर|के अंदर|के अन्दर)(?:\b|\s|$|[,\.\?!])",
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

        # Check cheap/budget cues across all languages
        if re.search(r"(?:\b|\s|^)(sasta|kam budget|sasti|kam daam|kami kharchat|cheap|budget friendly|low cost|किफायतशीर|सस्त|सुआणो)(?:\b|\s|$|[,\.\?!])", text):
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

        # Word numbers: "char log", "panch vyakti", "don jan", "team of six", "group of five"
        for word, val in NUMBER_WORDS.items():
            pattern = rf"(?:\b|\s|^)(?:(?:team|group)\s+of\s+|for\s+)?{re.escape(word)}\s*(?:people|persons|members|pax|seats|log|logo|lok|vyakti|jan|लोग|लोक|व्यक्ती)(?:\b|\s|$|[,\.\?!])"
            if re.search(pattern, text):
                return val
            if re.search(rf"(?:\b|\s|^)(?:team|group)\s+of\s+{re.escape(word)}(?:\b|\s|$|[,\.\?!])", text):
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

    @classmethod
    def extract_time_range(cls, text: str) -> tuple[str | None, str | None, float | None]:
        """Extract start_time, end_time, and duration_hours from time range expressions.

        Supports:
        - 'from 2 to 6 PM', '2 to 6 pm', '2pm to 6pm', 'from 14:00 to 18:00', '2:00 to 6:00 pm'
        - '10 am to 1 pm', '10:00 am - 1:00 pm'
        - '2 se 6 baje', '२ ते ६ वाजता'
        """
        range_match = re.search(
            r"(?:\bfrom\s+|\bbetween\s+)?(\d{1,2}(?::\d{2})?)\s*(am|pm)?\s*(?:to|-|till|until|se|te|ते|से)\s*(\d{1,2}(?::\d{2})?)\s*(am|pm)?\s*(?:baje|vajta|वाजता)?(?:\b|\s|$|[,\.\?!])",
            text,
            re.IGNORECASE,
        )
        if range_match:
            t1_str, ampm1, t2_str, ampm2 = range_match.groups()
            ampm1 = ampm1.lower() if ampm1 else None
            ampm2 = ampm2.lower() if ampm2 else None

            def parse_parts(s: str) -> tuple[int, int]:
                parts = s.split(":")
                return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0

            orig_h1, m1 = parse_parts(t1_str)
            orig_h2, m2 = parse_parts(t2_str)

            h1, h2 = orig_h1, orig_h2

            # Determine AM/PM for h2
            if ampm2 == "pm" and h2 < 12:
                h2 += 12
            elif ampm2 == "am" and h2 == 12:
                h2 = 0
            elif not ampm2 and 1 <= h2 <= 7:
                h2 += 12

            # Determine AM/PM for h1
            if ampm1:
                if ampm1 == "pm" and h1 < 12:
                    h1 += 12
                elif ampm1 == "am" and h1 == 12:
                    h1 = 0
            else:
                if ampm2 == "pm":
                    if orig_h1 < orig_h2 and h1 < 12:
                        h1 += 12
                    elif orig_h1 >= orig_h2 and orig_h1 >= 12:
                        pass
                elif ampm2 == "am":
                    if h1 == 12:
                        h1 = 0
                else:
                    if 1 <= orig_h1 <= 7:
                        h1 += 12

            start_str = f"{h1:02d}:{m1:02d}"
            end_str = f"{h2:02d}:{m2:02d}"
            duration = max(0.5, (h2 * 60 + m2 - (h1 * 60 + m1)) / 60.0)
            return start_str, end_str, duration

        return None, None, None

    @classmethod
    def extract_noise_preference(cls, text: str) -> str | None:
        """Extract noise/acoustic preference from query."""
        if re.search(
            r"(?:\b|\s|^)(quiet|silent|peaceful|shant|शांत|low noise|soundproof|soundproofing|whisper|calm|deep work|focused work|noise-free|quiet zone|silence|सुभीता|सुभीत|सुआणो|सुभीतो|आवाज नाही|आवाज निछ|शान्ति|चुपचाप)(?:\b|\s|$|[,\.\?!])",
            text,
        ):
            return "quiet"
        if re.search(
            r"(?:\b|\s|^)(lively|social|energetic|active|vibrant|party|event|networking)(?:\b|\s|$|[,\.\?!])",
            text,
        ):
            return "lively"
        if re.search(
            r"(?:\b|\s|^)(moderate|medium noise|open floor|normal)(?:\b|\s|$|[,\.\?!])",
            text,
        ):
            return "moderate"
        return None

    @classmethod
    def extract_privacy(cls, text: str) -> str | None:
        """Extract privacy preference from query."""
        if re.search(
            r"(?:\b|\s|^)(private|private room|private cabin|private workspace|cabin|enclosed|kamra|kholi|single room|private office|कमरा|खोली|कुटिया|स्वतंत्र खोली)(?:\b|\s|$|[,\.\?!])",
            text,
        ):
            return "private"
        if re.search(
            r"(?:\b|\s|^)(shared|open desk|hot desk|coworking|open space|community)(?:\b|\s|$|[,\.\?!])",
            text,
        ):
            return "shared"
        return None

    @classmethod
    def extract_landmark(cls, text: str) -> str | None:
        """Extract landmark references such as campus, university, metro, etc."""
        m = re.search(
            r"(?:\b|\s|^)(?:near|close to|around|by|javal|pas)?\s*(?:the\s+)?(campus|university|college|metro|station|airport|tech park|it park)(?:\b|\s|$|[,\.\?!])",
            text,
        )
        if m:
            return m.group(1).lower()
        return None

    @classmethod
    def extract_radius(cls, text: str) -> float | None:
        """Extract radius constraint in kilometers."""
        m = re.search(
            r"(?:within|under|in|radius\s+of)?\s*(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers|किलोमीटर)(?:\b|\s|$|[,\.\?!])",
            text,
        )
        if m:
            return float(m.group(1))
        return None

    @classmethod
    def extract_keywords(cls, text: str) -> list[str]:
        """Tokenize and return informative query keywords."""
        stopwords = {
            "a", "an", "the", "in", "on", "at", "for", "with", "and", "or",
            "to", "from", "of", "by", "is", "it", "me", "i", "need", "want",
            "find", "somewhere", "place", "space", "under", "below",
            "mein", "ko", "ke", "ka", "ki", "se", "par", "hai", "chahiye",
            "madhe", "yethe", "javal", "sathi", "ani", "sobat", "pahije", "aahe",
        }
        tokens = re.findall(r"\w+", text.lower())
        return [t for t in tokens if len(t) > 1 and t not in stopwords]

    @classmethod
    def build_semantic_query(
        cls,
        normalized: str,
        space_type: str | None,
        amenities: list[str],
        use_case: str | None,
        noise_pref: str | None,
        city: str | None,
    ) -> str:
        """Synthesize normalized semantic query text for embedding representation."""
        if not normalized:
            return ""
        # Clean query for embedding
        cleaned = re.sub(r"[^\w\s\-\u0900-\u097F]", " ", normalized)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        parts = [cleaned]
        if space_type and space_type not in cleaned:
            parts.append(space_type)
        if noise_pref and noise_pref not in cleaned:
            parts.append(f"{noise_pref} noise")
        if use_case and use_case not in cleaned:
            parts.append(use_case)
        return " ".join(parts)


RuleBasedQueryParser = QueryParser

