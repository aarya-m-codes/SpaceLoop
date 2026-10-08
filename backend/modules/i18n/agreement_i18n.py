"""Multilingual Section 52 Micro-Lease & Revocable License Agreement Generator.

Generates statutory temporary space use agreements under Section 52 of the
Indian Easements Act, 1882 in all six supported platform languages:
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
    LANG_JNS,
    LANG_KFY,
    LANG_MR,
    normalize_language_code,
)


def generate_multilingual_micro_lease(
    space_dict: dict[str, Any],
    booking_dict: dict[str, Any],
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Generate legally binding, statutory temporary license agreement in the requested language."""
    lang = normalize_language_code(language)

    booking_id = booking_dict.get("id", "NEW")
    space_title = space_dict.get("title", "SpaceLoop Verified Micro-Workspace")
    space_addr = space_dict.get("address", space_dict.get("location", "Registered SpaceLoop Premises"))
    host_name = space_dict.get("host_name", space_dict.get("owner_name", "Verified Property Host"))
    renter_name = booking_dict.get("renter_name", booking_dict.get("guest_name", "Verified SpaceLoop Seeker"))
    start_time = booking_dict.get("start_time", booking_dict.get("start_iso", "Scheduled Slot Start"))
    end_time = booking_dict.get("end_time", booking_dict.get("end_iso", "Scheduled Slot End"))
    hours = booking_dict.get("hours_booked", booking_dict.get("duration_hours", 2))
    total_price = booking_dict.get("total_price", booking_dict.get("amount", 200.0))
    escrow_deposit = booking_dict.get("deposit_held", booking_dict.get("escrow_deposit_amount", 100.0))
    purpose = booking_dict.get("intended_purpose", "Individual Academic Study / Remote Work")
    attendees = booking_dict.get("attendees_count", 1)

    # -------------------------------------------------------------
    # English
    # -------------------------------------------------------------
    if lang == LANG_EN:
        return f"""# SpaceLoop Temporary Micro-Lease & Access License
**Agreement ID:** SL-AGR-{booking_id}
**Statutory Classification:** Revocable License under Section 52 of the Indian Easements Act, 1882.
**Effective Window:** {start_time} to {end_time} ({hours} hours)

---

### 1. Parties & Premises
- **Grantor (Host / Licensor):** {host_name}
- **Grantee (Seeker / Licensee):** {renter_name}
- **Premises:** {space_title}, {space_addr}
- **Legal Character:** This instrument conveys a temporary, non-exclusive, revocable license strictly for the scheduled duration. It does NOT constitute a lease, tenancy, or right of continuous possession under any state rent control legislation.

---

### 2. Permitted Purpose & Occupancy
- **Authorized Purpose:** {purpose}
- **Maximum Permitted Occupants:** {attendees} person(s).
- **Prohibited Conduct:** Sublicensing, smoking, open flames, alcohol, commercial trading beyond permitted purpose, or excessive noise exceeding 55dB.

---

### 3. Financial Terms & Security Micro-Escrow
- **Usage Fee:** ₹{total_price} for {hours} hour(s) of access.
- **Micro-Escrow Deposit:** ₹{escrow_deposit} held via NPCI UPI automated escrow. Released instantly to the Seeker upon check-out visual clearance.
- **Overstay Clause:** Any unapproved overstay beyond a 10-minute grace period is charged at 1.5x the hourly rate in 30-minute blocks.

---

### 4. Zero-Hardware Access & Care Checklist
- **Entry Protocol:** Keyless check-in confirmed via 50m smartphone GPS geofence handshake and single-use digital pass.
- **Departure Protocol:** Licensee must restore furniture to initial positions, switch off all fans and lights, remove all personal waste, and capture an exit condition photo.

---

### 5. Mutual Indemnification
The Licensee agrees to exercise reasonable care and releases the Host and SpaceLoop Technologies from liability for personal injury or personal property loss occurring during the reservation window, save for willful host misconduct.

*Digitally sealed, timestamped, and bound upon booking authorization via SpaceLoop Platform.*"""

    # -------------------------------------------------------------
    # Hindi
    # -------------------------------------------------------------
    elif lang == LANG_HI:
        return f"""# स्पेस-लूप अस्थायी माइक्रो-अनुबंध एवं प्रवेश लाइसेंस
**अनुबंध संख्या:** SL-AGR-{booking_id}
**वैधानिक वर्गीकरण:** भारतीय सुखाचार अधिनियम 1882 की धारा 52 के अंतर्गत प्रतिसंहरणीय लाइसेंस।
**प्रभावी अवधि:** {start_time} से {end_time} ({hours} घंटे)

---

### 1. पक्षकार एवं परिसर
- **दाता (मेज़बान / लाइसेंसदाता):** {host_name}
- **ग्राही (सीकर / लाइसेंसी):** {renter_name}
- **परिसर:** {space_title}, {space_addr}
- **विधिक प्रकृति:** यह दस्तावेज केवल निर्धारित समय के लिए गैर-अनन्य, प्रतिसंहरणीय उपयोग का अधिकार देता है। यह किसी भी किरायेदारी या पट्टे का निर्माण नहीं करता।

---

### 2. अनुमत उपयोग एवं क्षमता
- **अधिकृत उद्देश्य:** {purpose}
- **अधिकतम अनुमत व्यक्ति:** {attendees}
- **निषिद्ध गतिविधियाँ:** उप-किरायेदारी, धूम्रपान, नशा, 55dB से अधिक ध्वनि, या अनाधिकृत व्यावसायिक कार्य।

---

### 3. वित्तीय शर्तें एवं सुरक्षा माइक्रो-एस्क्रो
- **उपयोग शुल्क:** ₹{total_price} ({hours} घंटों के लिए)।
- **माइक्रो-एस्क्रो सुरक्षा जमा:** ₹{escrow_deposit}। चेकआउट पर कमरे की सही स्थिति सत्यापित होने पर तुरंत वापस।
- **अति-प्रवास नियम:** 10 मिनट की छूट के बाद अनधिकृत ठहराव पर 1.5 गुना दर लागू होगी।

---

### 4. डिजिटल प्रवेश एवं प्रस्थान नियम
- **प्रवेश:** 50 मीटर जीपीएस जियोफेंस एवं 4-अंकीय डिजिटल पिन द्वारा।
- **प्रस्थान:** बिजली, पंखे बंद करें, कचरा हटाएं एवं प्रस्थान फ़ोटो अपलोड करें।

*स्पेस-लूप प्लेटफ़ॉर्म द्वारा डिजिटल रूप से सत्यापित एवं प्रलेखित।*"""

    # -------------------------------------------------------------
    # Marathi
    # -------------------------------------------------------------
    elif lang == LANG_MR:
        return f"""# स्पेस-लूप तात्पुरता मायक्रो-परवाना करार
**करार क्रमांक:** SL-AGR-{booking_id}
**कायदेशीर वर्गीकरण:** भारतीय सुखाधिकार कायदा 1882 च्या कलम 52 अंतर्गत रद्द करण्यायोग्य परवाना.
**कालावधी:** {start_time} ते {end_time} ({hours} तास)

---

### 1. पक्षकार आणि जागा
- **परवाना देणारा (होस्ट):** {host_name}
- **परवाना घेणारा (सीकर):** {renter_name}
- **जागा:** {space_title}, {space_addr}
- **कायदेशीर स्वरूप:** हा करार केवळ निर्धारित काळासाठी तात्पुरता वापर अधिकार देतो. कोणताही भाडेकरू हक्क तयार होत नाही.

---

### 2. अनुज्ञेय वापर आणि उपस्थिती
- **अधिकृत हेतू:** {purpose}
- **कमाल व्यक्ती मर्यादा:** {attendees}
- **प्रतिबंधित बाबी:** उप-भाडेतत्व, धुम्रपान, 55dB पेक्षा जास्त आवाज किंवा अनधिकृत व्यवहार.

---

### 3. आर्थिक अटी आणि सुरक्षा ठेव
- **वापर शुल्क:** ₹{total_price} ({hours} तासांसाठी).
- **मायक्रो-एस्क्रो ठेव:** ₹{escrow_deposit}. चेकआउट तपासणीनंतर त्वरित संपूर्ण परतावा.
- **अतिरिक्त वेळ:** 10 मिनिटांच्या सवलतीनंतर 1.5 पट दंड आकारला जाईल.

---

### 4. डिजिटल प्रवेश आणि स्वच्छता
- **प्रवेश:** 50 मीटर GPS जिओफेन्स आणि 4-अंकी पिन द्वारे.
- **निर्गमन:** विद्युत उपकरणे बंद करा, जागा स्वच्छ ठेवा आणि निर्गमन फोटो अपलोड करा.

*स्पेस-लूप प्लॅटफॉर्मद्वारे डिजिटल मुद्रांकित आणि प्रमाणित.*"""

    # -------------------------------------------------------------
    # Garhwali
    # -------------------------------------------------------------
    elif lang == LANG_GSW:
        return f"""# स्पेस-लूप अस्थायी ठौर उपयोग माइक्रो-लाइसेंस
**समझौता संख्या:** SL-AGR-{booking_id}
**कानूनी श्रेणी:** भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत प्रतिसंहरणीय (रद्द ह्वे सकणौ) लाइसेंस।
**मान्य बगत:** {start_time} बठे {end_time} तक ({hours} घंटा)

---

### 1. पक्ष अर ठौर
- **ठौर देण्ये (मेजबान / लाइसेंसदाता):** {host_name}
- **ठौर लेण्ये (सीकर / लाइसेंसी):** {renter_name}
- **ठौर को पत्तो:** {space_title}, {space_addr}
- **कानूनी रूप:** यि कागद सिर्फ तय बगत खातिर कमरे को अस्थायी उपयोग कर्नै छूट देद। येमा कखि भि पक्का किरायेदार बणनौ अधिकार निछ।

---

### 2. काम अर लोग
- **काम को उद्देश्य:** {purpose}
- **ज्यादा से ज्यादा लोग:** {attendees}
- **मना काम:** कसि और थै कमरा देण, बीड़ी-सिगरेट, नशा, 55dB से ज्यादा हल्लो-गुल्लो या गलत काम कर्नै सख्त मनाही छ।

---

### 3. रुप्या को हिसाब अर सुरक्षा अमानत
- **किराया:** ₹{total_price} ({hours} घंटा खातिर)।
- **सुरक्षा अमानत (एस्क्रो):** ₹{escrow_deposit}। काम खत्म ह्वे पर फोटो जांच का बाद ₹100 अमानत तुरंत फिर्ता मिल जालि।
- **ज्यादा रुकण पर:** 10 मिनट का बाद 1.5 गुना किराया लागलो।

---

### 4. कमरे मा जाण अर निकळण को नियम
- **प्रवेश:** 50 मीटर जीपीएस सीमा मा पुज्जण अर 4-अंकीय पिन से।
- **जाँदा बगत:** बत्ती-पंखा बंद करा, कमरा साफ करा अर निकळद बगत फोटो खिंचा।

*स्पेस-लूप प्लेटफ़ॉर्म द्वारा डिजिटल रूप से पक्का अर मुहरबंद।*"""

    # -------------------------------------------------------------
    # Kumaoni
    # -------------------------------------------------------------
    elif lang == LANG_KFY:
        return f"""# स्पेस-लूप अस्थायी जागा उपयोग माइक्रो-लाइसेंस
**समझौता संख्या:** SL-AGR-{booking_id}
**कानूनी वर्गीकरण:** भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत अस्थायी रद्द हुणे लाइसेंस।
**लागू बखत:** {start_time} बठे {end_time} तक ({hours} घण्टा)

---

### 1. पक्षकार अर जागा
- **जागा देणिया (मेजबान):** {host_name}
- **जागा लेणिया (सीकर):** {renter_name}
- **जागा:** {space_title}, {space_addr}
- **कानूनी आधार:** यो पत्र सिर्फ तय बखत खातिर जागा को अस्थायी उपयोग कर्नै अधिकार दिंद। येमे कसि भि किरायेदारी अधिकार न्है बन्द।

---

### 2. काम अर व्यक्ति संख्या
- **उद्देश्य:** {purpose}
- **अधिकतम व्यक्ति:** {attendees}
- **मनाई:** उप-किरायेदारी, नशा, धूम्रपान, 55dB बठे ज्यादा आवाज या अनुचित कार्य।

---

### 3. रुपिया को हिसाब अर अमानत
- **किराया:** ₹{total_price} ({hours} घण्टा खातिर)।
- **सुरक्षा अमानत:** ₹{escrow_deposit}। चेकआउट बखत सफाई जांच पूरी हुणे पर ₹100 अमानत तुरंत फिर्ता आ जालि।
- **अतिरिक्त बखत:** 10 मिनट की छूट का बाद 1.5 गुना दर लागू होल।

---

### 4. डिजिटल प्रवेश अर देखभाल
- **प्रवेश:** 50 मीटर GPS दायरा भितर 4-अंकीय पिन बठे।
- **जाँदा बखत:** बत्ती-पंखा बंद करा, जागा साफ करा अर फोटो अपलोड करा।

*स्पेस-लूप प्लेटफ़ॉर्म द्वारा डिजिटल रूप से सत्यापित अर सुरक्षित।*"""

    # -------------------------------------------------------------
    # Jaunsari
    # -------------------------------------------------------------
    else:  # LANG_JNS
        return f"""# स्पेस-लूप अस्थायी ठौर उपयोग माइक्रो-लाइसेंस
**समझौता संख्या:** SL-AGR-{booking_id}
**कानूनी वर्गीकरण:** भारतीय सुखाचार अधिनियम 1882 की धारा 52 का तहत अस्थायी लाइसेंस।
**लागू ओखत:** {start_time} बठे {end_time} तक ({hours} घंटे)

---

### 1. पक्षकार अर ठौर
- **ठौर देणो (मेजबान):** {host_name}
- **ठौर लेणो (सीकर):** {renter_name}
- **ठौर को पत्तो:** {space_title}, {space_addr}
- **कानूनी रूप:** ये दस्तावेज सिर्फ तय ओखत खातिर ठौर को अस्थायी उपयोग कर्नो अधिकार दे आ। येमा कसि भि किरायेदारी हक नाइ बणदो।

---

### 2. काम अर आदमियों की संख्या
- **उद्देश्य:** {purpose}
- **अधिकतम आदमी:** {attendees}
- **मनाई:** कसि और थै ठौर देणो, धूम्रपान, नशा, 55dB से ज्यादा आवाज कर्नो सख्त मना आ।

---

### 3. पिसों को हिसाब अर सुरक्षा अमानत
- **किराया:** ₹{total_price} ({hours} घंटे खातिर)।
- **सुरक्षा अमानत:** ₹{escrow_deposit}। काम पूरा होइ पर फोटो जांच का बाद ₹100 अमानत तुरंत फिर्ता होलि।
- **ज्यादा रुकणे पर:** 10 मिनट की छूट का बाद 1.5 गुना किराया लागलो।

---

### 4. कपाट खोलणो अर सफाई को नियम
- **प्रवेश:** 50 मीटर GPS सीमा मा पुज्जि के 4-अंकीय पिन से।
- **जाँदा ओखत:** बत्ती-पंखा बंद करा, ठौर साफ करा अर फोटो लगावा।

*स्पेस-लूप प्लेटफ़ॉर्म द्वारा डिजिटल रूप से पक्का अर मुहरबंद।*"""
