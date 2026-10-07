"""Domain lexicons, gazetteers, and multilingual synonyms for SpaceLoop NLP discovery.

Covers English, Hindi, Hinglish, and Marathi.
"""

from typing import Any

# City centroids (lat, lng)
CITY_CENTROIDS: dict[str, tuple[float, float]] = {
    "Bengaluru": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "New Delhi": (28.6139, 77.2090),
    "Pune": (18.5204, 73.8567),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Ahmedabad": (23.0225, 72.5714),
}

# Multilingual city name aliases
CITY_ALIASES: dict[str, str] = {
    # Bengaluru
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "blr": "Bengaluru",
    "बेंगलुरु": "Bengaluru",
    "बेंगलोर": "Bengaluru",
    "बंगळुरू": "Bengaluru",
    # Mumbai
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "bom": "Mumbai",
    "मुम्बई": "Mumbai",
    "मुंबई": "Mumbai",
    # Delhi
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "del": "New Delhi",
    "ncr": "New Delhi",
    "दिल्ली": "New Delhi",
    "नवी दिल्ली": "New Delhi",
    # Pune
    "pune": "Pune",
    "poona": "Pune",
    "पुणे": "Pune",
    # Hyderabad
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "हैदराबाद": "Hyderabad",
    # Gurgaon
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "गुड़गांव": "Gurgaon",
    "गुरुग्राम": "Gurgaon",
    # Noida
    "noida": "Noida",
    "नोएडा": "Noida",
    # Chennai
    "chennai": "Chennai",
    "madras": "Chennai",
    "चेन्नई": "Chennai",
    # Kolkata
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "कोलकाता": "Kolkata",
    # Ahmedabad
    "ahmedabad": "Ahmedabad",
    "amdavad": "Ahmedabad",
    "अहमदाबाद": "Ahmedabad",
}

# Neighborhoods with associated city and coordinates
NEIGHBORHOOD_MAP: dict[str, dict[str, Any]] = {
    "indiranagar": {
        "name": "Indiranagar",
        "city": "Bengaluru",
        "lat": 12.9784,
        "lng": 77.6408,
        "aliases": ["indiranagar", "indira nagar", "इंदिरानगर"],
    },
    "koramangala": {
        "name": "Koramangala",
        "city": "Bengaluru",
        "lat": 12.9352,
        "lng": 77.6245,
        "aliases": ["koramangala", "kora", "कोरामंगला"],
    },
    "whitefield": {
        "name": "Whitefield",
        "city": "Bengaluru",
        "lat": 12.9698,
        "lng": 77.7499,
        "aliases": ["whitefield", "व्हाइटफील्ड"],
    },
    "hsr": {
        "name": "HSR Layout",
        "city": "Bengaluru",
        "lat": 12.9121,
        "lng": 77.6446,
        "aliases": ["hsr", "hsr layout", "एचएसआर"],
    },
    "bkc": {
        "name": "BKC",
        "city": "Mumbai",
        "lat": 19.0657,
        "lng": 72.8687,
        "aliases": ["bkc", "bandra kurla complex", "बांद्रा कुर्ला", "बीकेसी"],
    },
    "bandra": {
        "name": "Bandra",
        "city": "Mumbai",
        "lat": 19.0596,
        "lng": 72.8295,
        "aliases": ["bandra", "बांद्रा"],
    },
    "andheri": {
        "name": "Andheri",
        "city": "Mumbai",
        "lat": 19.1197,
        "lng": 72.8464,
        "aliases": ["andheri", "अंधेरी"],
    },
    "lower parel": {
        "name": "Lower Parel",
        "city": "Mumbai",
        "lat": 18.9982,
        "lng": 72.8304,
        "aliases": ["lower parel", "लोअर परेल"],
    },
    "connaught place": {
        "name": "Connaught Place",
        "city": "New Delhi",
        "lat": 28.6315,
        "lng": 77.2167,
        "aliases": ["connaught place", "cp", "कनॉट प्लेस", "राजीव चौक"],
    },
    "hauz khas": {
        "name": "Hauz Khas",
        "city": "New Delhi",
        "lat": 28.5494,
        "lng": 77.2001,
        "aliases": ["hauz khas", "हौज़ खास"],
    },
    "cyber city": {
        "name": "Cyber City",
        "city": "Gurgaon",
        "lat": 28.4950,
        "lng": 77.0895,
        "aliases": ["cyber city", "dlf cyber city", "साइबर सिटी"],
    },
    "kothrud": {
        "name": "Kothrud",
        "city": "Pune",
        "lat": 18.5074,
        "lng": 73.8077,
        "aliases": ["kothrud", "कोथरूड"],
    },
    "hinjewadi": {
        "name": "Hinjewadi",
        "city": "Pune",
        "lat": 18.5913,
        "lng": 73.7389,
        "aliases": ["hinjewadi", "hinjawadi", "हिंजवडी"],
    },
    "viman nagar": {
        "name": "Viman Nagar",
        "city": "Pune",
        "lat": 18.5679,
        "lng": 73.9143,
        "aliases": ["viman nagar", "विमान नगर"],
    },
    "baner": {
        "name": "Baner",
        "city": "Pune",
        "lat": 18.5590,
        "lng": 73.7868,
        "aliases": ["baner", "बाणेर"],
    },
}

# Space typology mappings
SPACE_TYPE_SYNONYMS: dict[str, list[str]] = {
    "desk": [
        "desk", "hot desk", "dedicated desk", "hotdesk", "coworking desk",
        "mej", "मेज", "टेबल", "table", "workstation", "seat",
    ],
    "room": [
        "room", "private room", "cabin", "private cabin", "kamra", "कमरा",
        "kholi", "खोली", "private office", "enclosed room",
    ],
    "meeting_room": [
        "meeting room", "conference room", "boardroom", "meeting space", "meeting",
        "baithak", "बैठक", "discussion room", "conference hall", "meeting pod",
    ],
    "studio": [
        "studio", "podcast studio", "recording studio", "photo studio",
        "video studio", "art studio", "स्टुडिओ", "स्टूडियो", "sound booth",
    ],
    "commercial": [
        "commercial space", "retail space", "office space", "commercial",
        "dukaan", "दुकान", "showroom", "shop", "hall",
    ],
    "creative": [
        "creative space", "maker space", "art space", "workshop space", "craft studio",
    ],
}

# Amenity aliases
AMENITY_SYNONYMS: dict[str, list[str]] = {
    "wifi": ["wifi", "wi-fi", "internet", "fiber", "high speed net", "broadband", "वायफाय", "इंटरनेट"],
    "ac": ["ac", "a/c", "air condition", "air conditioning", "air conditioned", "cool", "hawa", "एसी"],
    "parking": ["parking", "car parking", "bike parking", "valet", "gaadi parking", "पार्किंग", "वाहन पार्किंग"],
    "power_backup": ["power backup", "inverter", "generator", "ups", "bijli", "uninterrupted power", "charging", "surge protector"],
    "quiet": ["quiet", "silent", "shant", "शांत", "soundproof", "soundproofing", "noise-free", "whisper", "peaceful", "shanti", "आवाज नाही"],
    "projector": ["projector", "screen", "display", "tv", "monitor", "4k display", "प्रोजेक्टर"],
    "whiteboard": ["whiteboard", "board", "marker", "व्हाइटबोर्ड", "फळा"],
    "coffee": ["coffee", "tea", "chai", "espresso", "चाय", "चहा", "beverages", "pantry", "cafe"],
    "washroom": ["washroom", "restroom", "toilet", "bathroom", "शौचालय"],
    "ergonomic_seating": ["ergonomic chair", "herman miller", "ergonomic seating", "comfortable seating", "ergonomic"],
}

# Use case categories
USE_CASE_SYNONYMS: dict[str, list[str]] = {
    "podcast": ["podcast", "podcasting", "recording", "voiceover", "audio", "पोडकास्ट", "ध्वनिमुद्रण"],
    "coding": ["coding", "programming", "hackathon", "software", "development", "coder", "developer", "deep work"],
    "study": ["study", "padhai", "पढ़ाई", "abhyas", "अभ्यास", "exam prep", "reading", "अभ्यासासाठी"],
    "meeting": ["meeting", "client meeting", "interview", "discussion", "board meeting", "team sync", "presentation"],
    "photoshoot": ["photoshoot", "photo shoot", "video shoot", "shooting", "filming", "photography"],
    "workshop": ["workshop", "training", "seminar", "meetup", "event", "class"],
}

# Multilingual number dictionary
NUMBER_WORDS: dict[str, int] = {
    "one": 1, "ek": 1, "एक": 1, "१": 1,
    "two": 2, "do": 2, "don": 2, "दोन": 2, "दो": 2, "२": 2,
    "three": 3, "teen": 3, "तीन": 3, "३": 3,
    "four": 4, "chaar": 4, "char": 4, "चार": 4, "४": 4,
    "five": 5, "paanch": 5, "panch": 5, "पाच": 5, "पांच": 5, "५": 5,
    "six": 6, "chhah": 6, "sah": 6, "सहा": 6, "छह": 6, "६": 6,
    "seven": 7, "saat": 7, "सात": 7, "७": 7,
    "eight": 8, "aath": 8, "आठ": 8, "८": 8,
    "nine": 9, "nau": 9, "नऊ": 9, "नौ": 9, "९": 9,
    "ten": 10, "das": 10, "daha": 10, "दहा": 10, "दस": 10, "१०": 10,
    "twenty": 20, "bees": 20, "vis": 20, "वीस": 20, "बीस": 20,
    "fifty": 50, "pachaas": 50, "pannaas": 50, "पन्नास": 50, "पचास": 50,
}
