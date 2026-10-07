import logging
import os
from typing import Any

logger = logging.getLogger("spaceloop.ai")


class SpaceAIAdapter:
    """AI adapter integrating Gemini with robust deterministic fallbacks.
    
    Guarantees that AI is NEVER a hard dependency for listing creation.
    """

    @staticmethod
    def scan_space(
        photo_url: str | None = None,
        space_type: str = "desk",
        category: str = "commercial",
        amenities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Extract environmental attributes (lighting, acoustics, power, uses)."""
        amenities = amenities or []
        api_key = os.getenv("GEMINI_API_KEY")

        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = (
                    f"Analyze this physical space listing ({space_type}, {category}) with amenities {amenities}. "
                    f"Provide concise values for: 1. Lighting quality, 2. Noise/acoustic level, 3. Power accessibility, 4. 3-4 Recommended uses. "
                    f"Format as JSON with keys: lighting, noise_level, power_access, recommended_uses."
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if response and response.text:
                    import json
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    parsed = json.loads(text.strip())
                    return {
                        "ai_lighting": parsed.get("lighting", "Natural ambient sunlight with overhead LED"),
                        "ai_noise_level": parsed.get("noise_level", "Quiet work zone (<42dB)"),
                        "ai_power_access": parsed.get("power_access", "Dedicated surge-protected outlets per station"),
                        "recommended_uses": parsed.get("recommended_uses", ["Focused Work", "Client Meetings"]),
                        "provider": "gemini-api",
                    }
            except Exception as exc:
                logger.warning(f"Gemini AI scan failed, engaging deterministic fallback: {exc}")

        # Deterministic contextual fallback based on space typology
        return SpaceAIAdapter._deterministic_scan_fallback(space_type, amenities)

    @staticmethod
    def _deterministic_scan_fallback(space_type: str, amenities: list[str]) -> dict[str, Any]:
        """Deterministic heuristic fallback when external AI is unavailable."""
        st = space_type.lower()
        amenities_lower = [a.lower() for a in amenities]

        has_soundproof = any("sound" in a or "quiet" in a or "podcast" in a for a in amenities_lower)
        has_backup = any("backup" in a or "generator" in a or "ups" in a for a in amenities_lower)

        if "studio" in st or "podcast" in st:
            lighting = "Multi-point 5600K Studio Lighting & Dimmable Ring Light"
            noise = "Acoustically Treated / Soundproofed (<30dB Studio Grade)"
            power = "Heavy-load AV Circuit with Dedicated Power Strips & Surge Protection"
            uses = ["Podcast Recording", "Voiceover Production", "Video Interviews", "Product Photography"]
        elif "meeting" in st or "boardroom" in st or "conference" in st:
            lighting = "Warm Architectural Recessed LEDs with Natural Perimeter Glazing"
            noise = "Enclosed Sound-dampened Meeting Room (<38dB)"
            power = "Conference Table Center Core: 4x Universal AC + Dual USB-C 65W"
            uses = ["Client Presentations", "Team Sprint Planning", "Board Meetings", "Remote Video Calls"]
        elif "private" in st or "cabin" in st or "office" in st:
            lighting = "Ergonomic Task Lighting + Generous Natural Daylight"
            noise = "Private Enclosed Space (<35dB Quiet Focus)"
            power = "Under-desk Cable Trunking with UPS Power Backup" if has_backup else "Under-desk Universal Outlets"
            uses = ["Confidential Strategy Calls", "High-focus Deep Work", "Solo Executive Productivity"]
        else:
            # Default Desk / Coworking
            lighting = "Balanced 4000K Natural White Ambient Lighting with Low Glare"
            noise = "Moderate Professional Coworking Ambience (<45dB)"
            power = "Desk-mounted Dual 3-pin Socket + 2x Fast Charging USB-A"
            uses = ["Software Development", "Remote Work", "Writing & Research", "Study Sessions"]

        if has_soundproof:
            noise = "Acoustically Isolated Pod (<28dB Whispering Quiet)"

        return {
            "ai_lighting": lighting,
            "ai_noise_level": noise,
            "ai_power_access": power,
            "recommended_uses": uses,
            "provider": "deterministic-fallback",
            "is_sensor_verified": False,
            "measurement_disclaimer": "Environmental metrics are architectural typology estimates, not on-site IoT sensor verified readings.",
        }

    @staticmethod
    def assist_listing(
        title: str | None = None,
        space_type: str = "desk",
        neighborhood: str | None = None,
        city: str | None = None,
        amenities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate high-converting space copy, rules, and smart pricing recommendations."""
        amenities = amenities or []
        city_str = city or "Bengaluru"
        hood_str = f" in {neighborhood}" if neighborhood else ""

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                prompt = (
                    f"Create an appealing listing for a {space_type}{hood_str}, {city_str} with amenities {amenities}. "
                    f"Provide JSON with: suggested_title, suggested_description, suggested_hourly_price_inr, suggested_rules, recommended_uses."
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if response and response.text:
                    import json
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    parsed = json.loads(text.strip())
                    return {
                        "suggested_title": parsed.get("suggested_title", f"Premium {space_type.title()} in {city_str}"),
                        "suggested_description": parsed.get("suggested_description", "Modern work environment."),
                        "suggested_hourly_price": float(parsed.get("suggested_hourly_price_inr", 200.0)),
                        "suggested_rules": parsed.get("suggested_rules", "Respect quiet hours. Keep workspace clean."),
                        "recommended_uses": parsed.get("recommended_uses", ["Focused Work", "Meetings"]),
                        "provider": "gemini-api",
                    }
            except Exception as exc:
                logger.warning(f"Gemini listing assist failed, using deterministic fallback: {exc}")

        # Deterministic listing assistance
        pricing_matrix = {
            "desk": 150.0,
            "private_office": 350.0,
            "cabin": 300.0,
            "meeting_room": 450.0,
            "studio": 600.0,
            "event_space": 1200.0,
        }
        suggested_price = pricing_matrix.get(space_type.lower(), 200.0)

        clean_title = title or f"Productive {space_type.replace('_', ' ').title()}{hood_str}, {city_str}"
        description = (
            f"Welcome to this premier {space_type.replace('_', ' ')} located{hood_str}, {city_str}. "
            f"Designed for modern professionals, this space offers uninterrupted high-speed internet, "
            f"ergonomic seating, and a collaborative yet focused environment. Ideal for solo creators and teams alike."
        )
        rules = "1. Please keep conversations at a moderate volume.\n2. No smoking inside the premises.\n3. Keep food and drinks at designated pantry areas."
        uses = ["Deep Focus Coding", "Client Discussions", "Creative Brainstorming"]

        return {
            "suggested_title": clean_title,
            "suggested_description": description,
            "suggested_hourly_price": suggested_price,
            "suggested_daily_price": round(suggested_price * 6.5, 2),
            "suggested_rules": rules,
            "recommended_uses": uses,
            "provider": "deterministic-fallback",
        }
