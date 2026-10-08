"""SpaceLoop Central Multilingual Lexicon & Message Catalog.

Provides dictionary resources, search matching explanations, error messages,
space taxonomy, amenity names, and deterministic conversational responses
across all six supported languages:
- English (en)
- Hindi (hi)
- Marathi (mr)
- Garhwali (gsw)
- Kumaoni (kfy)
- Jaunsari (jns)
"""

from typing import Any
from backend.modules.i18n.constants import (
    DEFAULT_LANGUAGE,
    LANG_EN,
    LANG_GSW,
    LANG_HI,
    LANG_HINGLISH,
    LANG_JNS,
    LANG_KFY,
    LANG_MR,
    normalize_language_code,
)

# -----------------------------------------------------------------------------
# 1. API Error Contracts
# -----------------------------------------------------------------------------
ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "BAD_REQUEST": {
        LANG_EN: "Malformed or invalid request payload.",
        LANG_HI: "अनुरोध पेलोड अमान्य या विकृत है।",
        LANG_MR: "विनंती पेलोड अवैध किंवा चुकीचा आहे.",
        LANG_GSW: "अनुरोध मा खोटि जानकारी छ।",
        LANG_KFY: "अनुरोध भितर खोटि जानकारी छु।",
        LANG_JNS: "अनुरोध मा गलत जानकारी आ।",
    },
    "UNAUTHORIZED": {
        LANG_EN: "Authentication required to access this resource.",
        LANG_HI: "इस संसाधन तक पहुँचने के लिए प्रमाणीकरण आवश्यक है।",
        LANG_MR: "या संसाधनात प्रवेश करण्यासाठी प्रमाणीकरण आवश्यक आहे.",
        LANG_GSW: "ये संसाधन खातिर लॉग-इन जरूरी छ।",
        LANG_KFY: "ये संसाधन देखण खातिर लॉग-इन जरूरी छु।",
        LANG_JNS: "ये जगा देखण खातिर लॉग-इन जरूरी आ।",
    },
    "FORBIDDEN": {
        LANG_EN: "You do not have permission to perform this action.",
        LANG_HI: "आपको यह क्रिया करने की अनुमति नहीं है।",
        LANG_MR: "तुम्हाला ही कृती करण्याची परवानगी नाही.",
        LANG_GSW: "तिमी थै यि काम कर्नै इजाजत निछ।",
        LANG_KFY: "तुम थै यो काम कर्नै इजाजत न्है।",
        LANG_JNS: "तुमे ये काम कर्नो अधिकार नाइ आ।",
    },
    "NOT_FOUND": {
        LANG_EN: "Requested resource was not found.",
        LANG_HI: "अनुरोधित संसाधन नहीं मिला।",
        LANG_MR: "विनंती केलेले संसाधन सापडले नाही.",
        LANG_GSW: "खोजे का ठौर या संसाधन नि मिलि।",
        LANG_KFY: "खोजे गयो ठौर या संसाधन नि मिल्यो।",
        LANG_JNS: "खोजेई जगा या संसाधन नाइ मिलो।",
    },
    "CONFLICT": {
        LANG_EN: "Resource conflict: slot already booked or state mismatch.",
        LANG_HI: "संसाधन विरोध: स्लॉट पहले से बुक है या स्थिति में विसंगति है।",
        LANG_MR: "संसाधन संघर्ष: स्लॉट आधीच बुक केला आहे.",
        LANG_GSW: "समय पहिलि हि बुक छ, टकराव ह्वैगे।",
        LANG_KFY: "बखत पैलि बठे बुक छु, टकराव भै गयो।",
        LANG_JNS: "ओखत पहिलै बुक आ, टकराव होइगो।",
    },
    "VALIDATION_ERROR": {
        LANG_EN: "Validation failed: please verify your input parameters.",
        LANG_HI: "सत्यापन विफल: कृपया अपने इनपुट की पुष्टि करें।",
        LANG_MR: "पडताळणी अयशस्वी: कृपया माहिती तपासा.",
        LANG_GSW: "जांच मा खोटि मिलि: अपणी जानकारी ठीक करा।",
        LANG_KFY: "जांच विफल भै: अपण जानकारी जांचा।",
        LANG_JNS: "जांच नाइ होइ: आपुणी जानकारी सही करा।",
    },
    "RATE_LIMITED": {
        LANG_EN: "Too many requests. Please slow down and try again.",
        LANG_HI: "बहुत अधिक अनुरोध। कृपया कुछ समय बाद पुनः प्रयास करें।",
        LANG_MR: "अति विनंत्या. कृपया थोड्या वेळाने प्रयत्न करा.",
        LANG_GSW: "घणा अनुरोध ह्वैगिन। थ्वाडा बगत बाद फिर करा।",
        LANG_KFY: "घणी रिक्वेस्ट आइ गेन। थ्वाड़ि देर में फिर करा।",
        LANG_JNS: "घणे अनुरोध होइगे। थ्वाड़ो ओखत रुकी के करा।",
    },
    "INTERNAL_SERVER_ERROR": {
        LANG_EN: "An internal platform error occurred. Please retry shortly.",
        LANG_HI: "प्लेटफ़ॉर्म पर आंतरिक त्रुटि हुई। कृपया थोड़ी देर में पुनः प्रयास करें।",
        LANG_MR: "अंतर्गत सर्व्हर त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
        LANG_GSW: "सर्वर मा गड़बड़ ह्वैगि। थ्वाडा बगत बाद कोशिश करा।",
        LANG_KFY: "सर्वर भितर गड़बड़ भै। थ्वाड़ि देर में दुबार करा।",
        LANG_JNS: "सर्वर मा गड़बड़ होइगि। थ्वाड़ो रुकी के फेर करा।",
    },
}

# -----------------------------------------------------------------------------
# 2. Taxonomy & Amenities
# -----------------------------------------------------------------------------
SPACE_TYPES: dict[str, dict[str, str]] = {
    "desk": {
        LANG_EN: "Desk",
        LANG_HI: "डेस्क",
        LANG_MR: "डेस्क",
        LANG_GSW: "मेज / डेस्क",
        LANG_KFY: "मेज / डेस्क",
        LANG_JNS: "मेज / डेस्क",
    },
    "room": {
        LANG_EN: "Private Room",
        LANG_HI: "निजी कमरा",
        LANG_MR: "स्वतंत्र खोली",
        LANG_GSW: "निजी खोली",
        LANG_KFY: "निजी खोली / कमरा",
        LANG_JNS: "निजी कमरा / खोली",
    },
    "meeting_room": {
        LANG_EN: "Meeting Room",
        LANG_HI: "मीटिंग रूम",
        LANG_MR: "बैठक कक्ष",
        LANG_GSW: "बैठक खोली",
        LANG_KFY: "बैठक कमरा",
        LANG_JNS: "बैठक कमरा",
    },
    "studio": {
        LANG_EN: "Studio",
        LANG_HI: "स्टूडियो",
        LANG_MR: "स्टुडिओ",
        LANG_GSW: "स्टूडियो / कला ठौर",
        LANG_KFY: "स्टूडियो",
        LANG_JNS: "स्टूडियो",
    },
    "commercial": {
        LANG_EN: "Commercial Space",
        LANG_HI: "व्यावसायिक स्थान",
        LANG_MR: "व्यावसायिक जागा",
        LANG_GSW: "व्यापारिक ठौर",
        LANG_KFY: "व्यापारिक जागा",
        LANG_JNS: "व्यापारिक ठौर",
    },
    "creative": {
        LANG_EN: "Creative Space",
        LANG_HI: "रचनात्मक स्थान",
        LANG_MR: "सर्जनशील जागा",
        LANG_GSW: "हुनर ठौर",
        LANG_KFY: "रचनात्मक जागा",
        LANG_JNS: "रचनात्मक ठौर",
    },
}

AMENITIES: dict[str, dict[str, str]] = {
    "wifi": {
        LANG_EN: "High-Speed WiFi",
        LANG_HI: "तेज़ वाई-फ़ाई",
        LANG_MR: "हाय-स्पीड वायफाय",
        LANG_GSW: "तेज वाई-फाई",
        LANG_KFY: "फास्ट वाई-फाई",
        LANG_JNS: "तेज वाई-फाई",
    },
    "ac": {
        LANG_EN: "Air Conditioning",
        LANG_HI: "वातानुकूलित (AC)",
        LANG_MR: "वातानुकूलित (AC)",
        LANG_GSW: "ठंडी हवा (AC)",
        LANG_KFY: "वातानुकूलित (AC)",
        LANG_JNS: "एसी (AC)",
    },
    "parking": {
        LANG_EN: "Vehicle Parking",
        LANG_HI: "वाहन पार्किंग",
        LANG_MR: "वाहन पार्किंग",
        LANG_GSW: "गाड़ी खड़ी कर्नै ठौर",
        LANG_KFY: "गाड़ी पार्किंग",
        LANG_JNS: "गाड़ी खड़ी कर्नो ठौर",
    },
    "power_backup": {
        LANG_EN: "Power Backup",
        LANG_HI: "पावर बैकअप / इन्वर्टर",
        LANG_MR: "पॉवर बॅकअप",
        LANG_GSW: "बिजली बैकअप",
        LANG_KFY: "बिजली बैकअप",
        LANG_JNS: "बिजली बैकअप",
    },
    "quiet": {
        LANG_EN: "Quiet Acoustic Environment",
        LANG_HI: "शांत वातावरण",
        LANG_MR: "शांत परिसर",
        LANG_GSW: "सुभीता शांत ठौर",
        LANG_KFY: "सुभीत शांत जागा",
        LANG_JNS: "सुआणो शांत ठौर",
    },
    "projector": {
        LANG_EN: "Projector / Display Screen",
        LANG_HI: "प्रोजेक्टर / स्क्रीन",
        LANG_MR: "प्रोजेक्टर / स्क्रीन",
        LANG_GSW: "प्रोजेक्टर स्क्रीन",
        LANG_KFY: "प्रोजेक्टर",
        LANG_JNS: "प्रोजेक्टर",
    },
    "whiteboard": {
        LANG_EN: "Whiteboard & Markers",
        LANG_HI: "व्हाइटबोर्ड",
        LANG_MR: "व्हाइटबोर्ड",
        LANG_GSW: "व्हाइटबोर्ड",
        LANG_KFY: "व्हाइटबोर्ड",
        LANG_JNS: "व्हाइटबोर्ड",
    },
    "coffee": {
        LANG_EN: "Tea / Coffee Pantry",
        LANG_HI: "चाय व कॉफ़ी",
        LANG_MR: "चहा आणि कॉफी",
        LANG_GSW: "चाय-कॉफी",
        LANG_KFY: "चाय-कॉफी",
        LANG_JNS: "चाय-कॉफी",
    },
    "washroom": {
        LANG_EN: "Clean Restroom",
        LANG_HI: "स्वच्छ शौचालय",
        LANG_MR: "स्वच्छ प्रसाधनगृह",
        LANG_GSW: "शौचालय",
        LANG_KFY: "शौचालय",
        LANG_JNS: "शौचालय",
    },
    "ergonomic_seating": {
        LANG_EN: "Ergonomic Seating",
        LANG_HI: "आरामदायक कुर्सियाँ",
        LANG_MR: "आरामदायी बैठक",
        LANG_GSW: "सुभीता कुर्सी",
        LANG_KFY: "सुभीत कुर्सी",
        LANG_JNS: "सुआणि कुर्सी",
    },
}

# -----------------------------------------------------------------------------
# 3. Search Matching Grounded Explanations
# -----------------------------------------------------------------------------
MATCH_EXPLANATION_TEMPLATES: dict[str, dict[str, str]] = {
    "capacity_match": {
        LANG_EN: "Fits {req} people (Capacity: {max})",
        LANG_HI: "{req} लोगों के लिए उपयुक्त (क्षमता: {max})",
        LANG_MR: "{req} लोकांसाठी योग्य (क्षमता: {max})",
        LANG_GSW: "{req} मनखियों खातिर ठीक (क्षमता: {max})",
        LANG_KFY: "{req} मनखियों खातिर ठीक (क्षमता: {max})",
        LANG_JNS: "{req} मनखियों खातिर ठीक (क्षमता: {max})",
    },
    "budget_match": {
        LANG_EN: "Within your ₹{budget:g}/hr budget (₹{rate:g}/hr)",
        LANG_HI: "आपके ₹{budget:g}/घंटे के बजट में (₹{rate:g}/घंटा)",
        LANG_MR: "आपल्या ₹{budget:g}/तास बजेटमध्ये (₹{rate:g}/तास)",
        LANG_GSW: "अपणा ₹{budget:g}/घंटा बजेट मा (₹{rate:g}/घंटा)",
        LANG_KFY: "अपण ₹{budget:g}/घण्टा बजेट भितर (₹{rate:g}/घण्टा)",
        LANG_JNS: "आपुणा ₹{budget:g}/घंटे पिसे मा (₹{rate:g}/घंटे)",
    },
    "rate_only": {
        LANG_EN: "Hourly Rate: ₹{rate:g}/hour",
        LANG_HI: "प्रति घंटा दर: ₹{rate:g}/घंटा",
        LANG_MR: "तासाचा दर: ₹{rate:g}/तास",
        LANG_GSW: "प्रति घंटा किराया: ₹{rate:g}/घंटा",
        LANG_KFY: "प्रति घण्टा दर: ₹{rate:g}/घण्टा",
        LANG_JNS: "प्रति घंटे दर: ₹{rate:g}/घंटे",
    },
    "distance": {
        LANG_EN: "{dist:.1f} km away in {loc}",
        LANG_HI: "{loc} में {dist:.1f} किमी दूरी पर",
        LANG_MR: "{loc} मध्ये {dist:.1f} किमी अंतरावर",
        LANG_GSW: "{loc} मा {dist:.1f} किमी दूर",
        LANG_KFY: "{loc} भितर {dist:.1f} किमी दूर",
        LANG_JNS: "{loc} मा {dist:.1f} किमी दूर",
    },
    "location_only": {
        LANG_EN: "Located in {loc}",
        LANG_HI: "{loc} में स्थित",
        LANG_MR: "{loc} येथे स्थित",
        LANG_GSW: "{loc} मा स्थित छ",
        LANG_KFY: "{loc} भितर स्थित छु",
        LANG_JNS: "{loc} मा स्थित आ",
    },
    "quiet_environment": {
        LANG_EN: "Verified quiet environment",
        LANG_HI: "सत्यापित शांत कार्यक्षेत्र",
        LANG_MR: "पडताळणी झालेला शांत परिसर",
        LANG_GSW: "सुभीता शांत ठौर (आवाज निछ)",
        LANG_KFY: "सुभीत शांत जागा",
        LANG_JNS: "सुआणो शांत ठौर",
    },
    "available_slot": {
        LANG_EN: "Available on {date}{time}{dur}",
        LANG_HI: "{date}{time}{dur} पर उपलब्ध",
        LANG_MR: "{date}{time}{dur} रोजी उपलब्ध",
        LANG_GSW: "{date}{time}{dur} मा मिल सकद",
        LANG_KFY: "{date}{time}{dur} बखत उपलब्ध छु",
        LANG_JNS: "{date}{time}{dur} ओखत उपलब्ध आ",
    },
    "host_trust": {
        LANG_EN: "Verified host ({score}% trust score)",
        LANG_HI: "सत्यापित मेज़बान ({score}% ट्रस्ट स्कोर)",
        LANG_MR: "पडताळणी झालेला यजमान ({score}% विश्वास गुण)",
        LANG_GSW: "सत्यापित मेजबान ({score}% विश्वास स्कोर)",
        LANG_KFY: "सत्यापित मेजबान ({score}% विश्वास स्कोर)",
        LANG_JNS: "सत्यापित मेजबान ({score}% विश्वास स्कोर)",
    },
}

# -----------------------------------------------------------------------------
# 4. Deterministic Concierge (LoopBot) Responses across all 6 Languages
# -----------------------------------------------------------------------------
DETERMINISTIC_RESPONSES: dict[str, dict[str, str]] = {
    # ---------------- English ----------------
    LANG_EN: {
        "welcome": (
            "Hello! I am LoopBot, your SpaceLoop AI concierge. I can help you discover physical workspaces, "
            "calculate ₹100 micro-escrow quotes, explain our 5% fee & Section 52 micro-leases, or guide you through PIN check-in."
        ),
        "search": (
            "I can help you find verified physical spaces in {loc_str}{budget_info}. "
            "SpaceLoop matches listings using acoustic noise levels, high-speed WiFi, "
            "and host trust scores. Click below to browse active spaces or refine your filters."
        ),
        "booking": (
            "To book a space on SpaceLoop: 1) Run an instant precheck to verify slot availability and minimum hours. "
            "2) Submit your reservation. 3) Once the host accepts, you'll receive a secure 4-digit arrival PIN for physical access."
        ),
        "cancellation": (
            "SpaceLoop cancellation policy: When you cancel a booking, SpaceLoop retains only the 5% platform fee. "
            "You receive 100% of your rental subtotal plus 100% of the ₹100 security deposit refunded. "
            "If the host rejects your booking, you receive a full 100% refund."
        ),
        "access": (
            "For keyless check-in: 1) Enter your 4-digit arrival PIN at the door. 2) Your phone confirms you are within "
            "the 50-meter GPS geofence. 3) Upload quick check-in inspection photos to document space condition."
        ),
        "escrow": (
            "SpaceLoop micro-escrow pricing model: Space Subtotal = hourly rate × duration hours. Platform fee = 5% of subtotal. "
            "Refundable security deposit = ₹100.00. Total paid = Subtotal + 5% Fee + ₹100. Upon clean checkout, ₹100 is instantly returned."
        ),
        "host": (
            "To list your space on SpaceLoop: Upload photos, set your hourly rate and capacity, and verify your Discom electricity bill. "
            "After a session completes, your payout is released directly to your verified UPI VPA with zero subscription fees."
        ),
        "legal": (
            "All SpaceLoop reservations operate as a Leave and License under Section 52 of the Indian Easements Act, 1882. "
            "This creates a revocable personal license to occupy the workspace for the booked hours. No tenancy rights are created."
        ),
        "trust": (
            "SpaceLoop protects hosts and seekers with an Objective Trust Score (0-100), government KYC identity verification, "
            "and automated micro-escrow protection. In case of dispute, escrow funds are frozen until adjudication."
        ),
    },

    # ---------------- Hinglish ----------------
    LANG_HINGLISH: {
        "welcome": (
            "Namaste! Main LoopBot hoon, aapka SpaceLoop concierge. Main spaces dhoondhne, booking precheck, "
            "5% fee rules, aur PIN check-in mein aapki madad kar sakta hoon."
        ),
        "search": (
            "Main aapke liye {loc_str} mein verified physical {space_type}s dhoondh sakta hoon{budget_info}. "
            "Sabhi spaces mein high-speed WiFi aur 4-digit arrival PIN access available hai. "
            "Neeche diye gaye options se active spaces browse karein."
        ),
        "booking": (
            "SpaceLoop par book karne ke liye: 1) Slot availability aur minimum hours precheck karein. "
            "2) Reservation submit karein. 3) Host accept karne par physical entry ke liye 4-digit arrival PIN milega."
        ),
        "cancellation": (
            "SpaceLoop cancellation policy ke mutabik: Agar aap booking cancel karte hain, toh SpaceLoop sirf "
            "5% platform fee retain karta hai. Aapko rental subtotal ka 100% plus ₹100 security deposit pura wapas milta hai."
        ),
        "access": (
            "Check-in karne ke liye aapko 50m GPS geofence ke andar hona hoga aur apna 4-digit arrival PIN ya "
            "QR code use karna hoga. Saath hi inspection photos upload karke entry confirm karein."
        ),
        "escrow": (
            "SpaceLoop pricing formula: Total = Space Subtotal (hourly rate × hours) + 5% platform fee + ₹100 refundable escrow deposit. "
            "Checkout par ₹100 deposit aapko pura refund mil jata hai."
        ),
        "host": (
            "SpaceLoop par apni space list karne ke liye: Photos upload karein, hourly rate set karein, aur KYC complete karein. "
            "Booking complete hone par payment seedhe aapke UPI VPA par release hoti hai."
        ),
        "legal": (
            "All SpaceLoop reservations operate as a Leave and License under Section 52 of the Indian Easements Act, 1882. "
            "Isse sirf temporary license banta hai, koi tenancy rights nahi milte."
        ),
        "trust": (
            "SpaceLoop hosts aur seekers dono ko Objective Trust Score (0-100), KYC identity verification, "
            "aur automated micro-escrow se protect karta hai."
        ),
    },

    # ---------------- Hindi ----------------
    LANG_HI: {
        "welcome": (
            "नमस्ते! मैं लूपबॉट (LoopBot) हूँ, स्पेस-लूप का AI सहायक। मैं कार्यक्षेत्र खोजने, ₹100 माइक्रो-एस्क्रो उद्धरण, "
            "5% प्लेटफ़ॉर्म शुल्क व धारा 52 लीव-एंड-लाइसेंस नियमों को समझाने और पिन चेक-इन में आपकी सहायता कर सकता हूँ।"
        ),
        "search": (
            "मैं आपके लिए {loc_str} में सत्यापित कार्यक्षेत्र खोजने में सहायता कर सकता हूँ{budget_info}। "
            "स्पेस-लूप उच्च गति वाई-फ़ाई, शांत वातावरण और सत्यापित मेज़बानों के आधार पर परिणाम प्रस्तुत करता है।"
        ),
        "booking": (
            "स्पेस-लूप पर बुकिंग करने के लिए: 1) उपलब्धता जांचें। 2) आरक्षण प्रस्तुत करें। "
            "3) मेज़बान द्वारा स्वीकार किए जाने पर कमरे में प्रवेश के लिए 4-अंकीय आगमन पिन प्राप्त करें।"
        ),
        "cancellation": (
            "स्पेस-लूप रद्दीकरण नीति: बुकिंग रद्द करने पर केवल 5% प्लेटफ़ॉर्म शुल्क रखा जाता है। "
            "आपको 100% किराया और ₹100 सुरक्षा जमा राशि पूरी वापस मिलती है। मेज़बान द्वारा अस्वीकार होने पर पूरा 100% रिफ़ंड मिलता है।"
        ),
        "access": (
            "डिजिटल चेक-इन के लिए: 1) दरवाज़े पर अपना 4-अंकीय आगमन पिन दर्ज करें। 2) 50 मीटर जीपीएस जियोफेंस के भीतर उपस्थिति की पुष्टि करें। "
            "3) कमरे की प्रारंभिक स्थिति की फ़ोटो अपलोड करें। चेकआउट पर फ़ोटो अपलोड करने पर ₹100 जमा तुरंत वापस मिल जाती है।"
        ),
        "escrow": (
            "स्पेस-लूप मूल्य निर्धारण: कुल राशि = किराया उप-योग (दर × घंटे) + 5% प्लेटफ़ॉर्म शुल्क + ₹100 रिफ़ंडेबल सुरक्षा जमा। "
            "सत्र समाप्त होने पर ₹100 जमा राशि आपके खाते में वापस भेज दी जाती है।"
        ),
        "host": (
            "अपनी जगह सूचीबद्ध करने के लिए: फ़ोटो अपलोड करें, प्रति घंटा दर निर्धारित करें, और बिजली बिल सत्यापित करें। "
            "सत्र पूरा होने पर भुगतान सीधे आपके सत्यापित UPI VPA में बिना किसी सदस्यता शुल्क के भेजा जाता है।"
        ),
        "legal": (
            "स्पेस-लूप के सभी आरक्षण भारतीय सुखाचार अधिनियम 1882 की धारा 52 के तहत प्रतिसंहरणीय लीव-एंड-लाइसेंस के रूप में संचालित होते हैं। "
            "इससे केवल निर्धारित घंटों के लिए उपयोग का अधिकार मिलता है, कोई किरायेदारी अधिकार नहीं बनता।"
        ),
        "trust": (
            "स्पेस-लूप ऑब्जेक्टिव ट्रस्ट स्कोर (0-100), सरकारी पहचान सत्यापन और स्वचालित एस्क्रो द्वारा सुरक्षा प्रदान करता है।"
        ),
    },

    # ---------------- Marathi ----------------
    LANG_MR: {
        "welcome": (
            "नमस्कार! मी लूपबॉट (LoopBot), स्पेस-लूपचा AI सहाय्यक. मी जागा शोधणे, ₹100 मायक्रो-एस्क्रो अनामत, "
            "5% प्लॅटफॉर्म शुल्क, कलम 52 परवाना नियम आणि चेक-इन पिन बाबत आपली मदत करू शकतो."
        ),
        "search": (
            "मी आपल्यासाठी {loc_str} मधील खात्रीशीर जागा शोधू शकतो{budget_info}. "
            "स्पेस-लूप हाय-स्पीड वायफाय, शांत परिसर आणि होस्ट ट्रस्ट स्कोअरच्या आधारे योग्य जागा मिळवून देते."
        ),
        "booking": (
            "स्पेस-लूपवर जागा बुक करण्यासाठी: 1) स्लॉट उपलब्धता तपासा. 2) आरक्षण सबमिट करा. "
            "3) होस्टने स्वीकारल्यानंतर जागेत प्रवेश करण्यासाठी 4-अंकी पिन मिळवा."
        ),
        "cancellation": (
            "स्पेस-लूप रद्द करण्याचे धोरण: बुकिंग रद्द केल्यास केवळ 5% प्लॅटफॉर्म शुल्क कापले जाते. "
            "आपल्याला 100% भाडे आणि ₹100 सुरक्षा ठेव पूर्ण परत मिळते. होस्टने नाकारल्यास 100% संपूर्ण परतावा मिळतो."
        ),
        "access": (
            "विना-किल्ली प्रवेश: 1) दरवाजावर आपला 4-अंकी पिन टाका. 2) 50 मीटर GPS जिओफेन्स पडताळणी पूर्ण करा. "
            "3) खोलीच्या स्थितीचे फोटो अपलोड करा. चेकआउटनंतर ₹100 अनामत त्वरित परत केली जाते."
        ),
        "escrow": (
            "स्पेस-लूप शुल्क नियम: एकूण रक्कम = भाडे उप-योग + 5% प्लॅटफॉर्म शुल्क + ₹100 सुरक्षा ठेव. "
            "सत्र समाधानकारक संपल्यावर ₹100 ठेव थेट आपल्या खात्यात जमा होते."
        ),
        "host": (
            "आपली जागा सूचीबद्ध करण्यासाठी: फोटो अपलोड करा, तासाचा दर ठरवा आणि वीज बिल पडताळणी करा. "
            "सत्र संपल्यावर मोबदला थेट आपल्या UPI VPA वर जमा होतो."
        ),
        "legal": (
            "सर्व बुकिंग्ज भारतीय सुखाधिकार कायदा 1882 च्या कलम 52 अंतर्गत रद्द करण्यायोग्य लीव्ह आणि परवाना आहेत. "
            "यामुळे कोणताही भाडेकरू हक्क तयार होत नाही."
        ),
        "trust": (
            "स्पेस-लूप ऑब्जेक्टिव्ह ट्रस्ट स्कोअर, अधिकृत KYC पडताळणी आणि स्वयंचलित एस्क्रो द्वारे सुरक्षा पुरवते."
        ),
    },

    # ---------------- Garhwali ----------------
    LANG_GSW: {
        "welcome": (
            "पैलाग / प्रणाम! मी लूपबॉट (LoopBot) छौं, स्पेस-लूप को AI सहायक। मी तुम थै कार्यक्षेत्र खोजण, "
            "₹100 सुरक्षा अमानत, 5% प्लेटफ़ॉर्म शुल्क, धारा 52 लीव-लाइसेंस अर 4-अंकीय पिन चेक-इन मा मदद करि सकदौं।"
        ),
        "search": (
            "मी तुम खातिर {loc_str} मा बढ़िया ठौर खोजि सकदौं{budget_info}। "
            "स्पेस-लूप मा तेज वाई-फाई, शांत सुभीता अर भरोसेमंद मेजबान मिलदन।"
        ),
        "booking": (
            "ठौर बुक कर्नै खातिर: 1) पहिलि बगत जाँचा। 2) बुकिंग भेजा। "
            "3) मेजबान जब मान जाला, त कमरे मा जाण खातिर 4-अंकीय आगमन पिन मिल जालो।"
        ),
        "cancellation": (
            "रद्दीकरण नियम: अगर तिमी बुकिंग रद्द करदा, त स्पेस-लूप सिर्फ 5% शुल्क राखद। "
            "तुम थै 100% किराया अर ₹100 अमानत पूरी वापस मिलदी। मेजबान मना करला त पूरो 100% रुप्या वापस हुंद।"
        ),
        "access": (
            "कमरे मा जाण खातिर: 1) दरवाज पर अपणु 4-अंकीय पिन दबावा। 2) 50 मीटर GPS सीमा मा पुज्जा। "
            "3) कमरे की फोटो खींचा अर चेक-इन करा। चेकआउट पर फोटो खिंचिक ₹100 अमानत तुरंत फिर्ता मिल जालि।"
        ),
        "escrow": (
            "रुप्या को हिसाब: पूरो रुप्या = किराया + 5% प्लेटफ़ॉर्म शुल्क + ₹100 सुरक्षा अमानत। "
            "काम खत्म ह्वे पर ₹100 अमानत तिमी थै तुरंत वापस मिल जांद।"
        ),
        "host": (
            "अपणु ठौर जोड्ण खातिर: फोटो अपलोड करा, प्रति घंटा किराया रखा अर बिजली बिल सत्यापित करा। "
            "सत्र पूरा ह्वे पर रुप्या सीधै तुमरा UPI खाता मा आंद।"
        ),
        "legal": (
            "यि समझौता भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत अस्थायी लीव-एंड-लाइसेंस छ। "
            "येमा कखि भि पक्का किरायेदार बणनौ अधिकार निछ।"
        ),
        "trust": (
            "स्पेस-लूप ऑब्जेक्टिव ट्रस्ट स्कोर (0-100) अर सरकारी KYC से पूरी सुरक्षा अर विश्वास देद।"
        ),
    },

    # ---------------- Kumaoni ----------------
    LANG_KFY: {
        "welcome": (
            "पैलाग! मैं लूपबॉट (LoopBot) छुं, स्पेस-लूप को AI सहायक। मैं तुम थै काम कर्नै जागा खोजण, "
            "₹100 सुरक्षा अमानत, 5% प्लेटफ़ॉर्म शुल्क, धारा 52 लीव-लाइसेंस अर पिन चेक-इन भितर मदद कर सकूँछुं।"
        ),
        "search": (
            "मैं तुम खातिर {loc_str} भितर बढ़िया ठौर ढूंढि सकूँछुं{budget_info}। "
            "स्पेस-लूप भितर फास्ट वाई-फाई, शांत सुभीत माहौल अर सत्यापित मेजबान मिलन।"
        ),
        "booking": (
            "जागा बुक कर्नै खातिर: 1) बखत की जांच करा। 2) बुकिंग सबमिट करा। "
            "3) मेजबान स्वीकार करल त कमरे भितर जाँण खातिर 4-अंकीय आगमन पिन मिल जालो।"
        ),
        "cancellation": (
            "रद्दीकरण नियम: अगर तुम बुकिंग रद्द करला, त स्पेस-लूप केवल 5% प्लेटफ़ॉर्म शुल्क राखल। "
            "तुम थै 100% किराया अर ₹100 अमानत फिर्ता मिल जाली। मेजबान मना करल त पूरो 100% फिर्ता भै जालो।"
        ),
        "access": (
            "जागा भितर जाँण खातिर: 1) दरवाज पर 4-अंकीय पिन लगावा। 2) 50 मीटर GPS सीमा भितर उपस्थिति पक्की करा। "
            "3) चेक-इन फोटो अपलोड करा। चेकआउट बखत फोटो अपलोड कर्नै पर ₹100 अमानत तुरंत फिर्ता मिल जालि।"
        ),
        "escrow": (
            "रुपिया को हिसाब: कुल रुपिया = किराया + 5% प्लेटफ़ॉर्म शुल्क + ₹100 सुरक्षा अमानत। "
            "सत्र पूरा भै गयो त ₹100 अमानत सीधै फिर्ता आ जालि।"
        ),
        "host": (
            "अपण जागा लिस्ट कर्न खातिर: फोटो अपलोड करा, प्रति घण्टा दर तय करा अर बिजली बिल जाँचा। "
            "सत्र पूरा हुणे पर रुपिया सीधै तुमर UPI खाता भितर आ जालो।"
        ),
        "legal": (
            "यो समझौता भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत अस्थायी लीव-एंड-लाइसेंस छु। "
            "येमे कसि भि किरायेदारी अधिकार न्है बन्द।"
        ),
        "trust": (
            "स्पेस-लूप ट्रस्ट स्कोर (0-100), सरकारी पहचान जांच अर सुरक्षित एस्क्रो बठे पूरी सुरक्षा दिंद।"
        ),
    },

    # ---------------- Jaunsari ----------------
    LANG_JNS: {
        "welcome": (
            "नमस्ते / प्रणाम! आऊँ लूपबॉट (LoopBot) आ, स्पेस-लूप को AI सहायक। आऊँ तुमे काम कर्नो ठौर खोजणे, "
            "₹100 अमानत, 5% प्लेटफ़ॉर्म फीस, धारा 52 लीव-लाइसेंस अर पिन चेक-इन मा मदद करी सकूँ।"
        ),
        "search": (
            "आऊँ तुमारो खातिर {loc_str} मा सुआणो ठौर हेरी सकूँ{budget_info}। "
            "स्पेस-लूप मा तेज वाई-फाई, शांत सुभीतो माहौल अर सत्यापित मेजबान मिलदे।"
        ),
        "booking": (
            "ठौर बुक कर्नो खातिर: 1) ओखत हेरा। 2) बुकिंग करा। "
            "3) मेजबान मान जालो त कमरे मा जाण खातिर 4-अंकीय आगमन पिन मिल जालो।"
        ),
        "cancellation": (
            "रद्द कर्नो नियम: अगर तुमे बुकिंग रद्द करदे, त स्पेस-लूप सिर्फ 5% फीस राखदो। "
            "तुमे 100% किराया अर ₹100 अमानत पूरी वापस मिलदी। मेजबान मना करलो त पूरा 100% पिसे फिर्ता होलो।"
        ),
        "access": (
            "ठौर मा जाण खातिर: 1) कपाट पर 4-अंकीय पिन लगावा। 2) 50 मीटर GPS सीमा मा पुज्जा। "
            "3) चेक-इन फोटो खिंचा। चेकआउट मा फोटो खिंचणे पर ₹100 अमानत तुरंत फिर्ता मिल जालि।"
        ),
        "escrow": (
            "पिसों को हिसाब: पूरा रुपिया = किराया + 5% फीस + ₹100 अमानत। "
            "ओखत पूरा होइ पर ₹100 अमानत तुमारो खाता मा सीधै वापस होलि।"
        ),
        "host": (
            "आपुणो ठौर जोड्णो खातिर: फोटो लगावा, प्रति घंटे किराया रखा अर बिजली बिल सत्यापित करा। "
            "काम होइ पर पिसे सीधै तुमारो UPI खाता मा मिलदे।"
        ),
        "legal": (
            "ये समझौता भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत अस्थायी लीव-एंड-लाइसेंस आ। "
            "येमा कसि भि किरायेदारी हक नाइ बणदो।"
        ),
        "trust": (
            "स्पेस-लूप ट्रस्ट स्कोर (0-100), सरकारी KYC जांच अर सुरक्षित एस्क्रो से पूरी सुरक्षा दे आ।"
        ),
    },
}


def localize_error(code: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Return localized error message for standard error code."""
    lang = normalize_language_code(language)
    err_dict = ERROR_MESSAGES.get(code, ERROR_MESSAGES["INTERNAL_SERVER_ERROR"])
    return err_dict.get(lang, err_dict.get(DEFAULT_LANGUAGE, "An error occurred."))


def localize_space_type(space_type: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Return localized name for space type code."""
    lang = normalize_language_code(language)
    st = str(space_type or "desk").strip().lower()
    return SPACE_TYPES.get(st, {}).get(lang, space_type.title())


def localize_amenity(amenity: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Return localized name for amenity code."""
    lang = normalize_language_code(language)
    am = str(amenity or "").strip().lower()
    return AMENITIES.get(am, {}).get(lang, amenity.replace("_", " ").title())


def get_deterministic_response(intent: str, language: str = DEFAULT_LANGUAGE, context_vars: dict[str, Any] | None = None) -> str:
    """Retrieve grounded deterministic LoopBot response in the requested language."""
    clean_lang = str(language or "").strip().lower()
    if clean_lang == LANG_HINGLISH:
        lang = LANG_HINGLISH
    else:
        lang = normalize_language_code(language)
    lang_responses = DETERMINISTIC_RESPONSES.get(lang, DETERMINISTIC_RESPONSES[DEFAULT_LANGUAGE])
    template = lang_responses.get(intent) or lang_responses.get("welcome", "")
    if context_vars:
        try:
            return template.format(**context_vars)
        except Exception:
            return template
    return template
