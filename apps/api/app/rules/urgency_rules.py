from __future__ import annotations

from app.utils.parsers import normalize_text

EMERGENCY_KEYWORDS = {
    "chest pain",
    "shortness of breath",
    "unable to breathe",
    "severe bleeding",
    "stroke",
    "one sided weakness",
    "fainting",
}

URGENT_KEYWORDS = {
    "high fever",
    "fever",
    "vomiting",
    "dehydration",
    "severe pain",
    "infection",
    "rash spreading",
    "can not swallow",
}

SPECIALTY_HINTS: dict[str, tuple[list[str], str]] = {
    "throat": (["Family Medicine", "ENT"], "general_practitioner"),
    "cough": (["Family Medicine", "Urgent Care"], "general_practitioner"),
    "fever": (["Family Medicine", "Urgent Care"], "urgent_care"),
    "rash": (["Dermatology"], "specialist"),
    "skin": (["Dermatology"], "specialist"),
    "stomach": (["Internal Medicine", "Gastroenterology"], "general_practitioner"),
    "nausea": (["Internal Medicine", "Gastroenterology"], "general_practitioner"),
    "sinus": (["ENT"], "specialist"),
    "ear": (["ENT"], "specialist"),
    "period": (["OB-GYN"], "specialist"),
    "pelvic": (["OB-GYN"], "specialist"),
}


def evaluate_urgency(symptom_text: str, duration_days: int | None) -> dict[str, object]:
    normalized = normalize_text(symptom_text)
    red_flags = [phrase for phrase in EMERGENCY_KEYWORDS if phrase in normalized]
    matched_specialties: list[str] = []
    care_type = "general_practitioner"

    for keyword, (specialties, inferred_care_type) in SPECIALTY_HINTS.items():
        if keyword in normalized:
            matched_specialties.extend(specialties)
            if inferred_care_type == "specialist":
                care_type = "specialist"
            elif care_type != "specialist":
                care_type = inferred_care_type

    if red_flags:
        return {
            "urgency_level": "emergency",
            "care_type": "emergency",
            "red_flags": red_flags,
            "matched_specialties": sorted(set(matched_specialties)) or ["Emergency Medicine"],
            "summary": "Some symptoms may represent an emergency condition.",
            "next_step": "Seek emergency care immediately or call 911.",
        }

    urgent_hits = [phrase for phrase in URGENT_KEYWORDS if phrase in normalized]
    long_duration = duration_days is not None and duration_days >= 7

    if urgent_hits:
        urgency_level = "urgent"
        next_step = "Consider same-day urgent care or the earliest available clinician visit."
        if care_type == "general_practitioner":
            care_type = "urgent_care"
    elif long_duration:
        urgency_level = "soon"
        next_step = "Book a primary care or specialist visit within the next few days."
    elif any(term in normalized for term in ["mild", "monitor", "allergy", "itchy"]):
        urgency_level = "self-care"
        next_step = "Monitor symptoms, use self-care, and escalate if symptoms worsen."
    else:
        urgency_level = "routine"
        next_step = "A routine visit with a primary care doctor is a reasonable starting point."

    if not matched_specialties:
        matched_specialties = ["Family Medicine", "Internal Medicine"]

    return {
        "urgency_level": urgency_level,
        "care_type": care_type,
        "red_flags": urgent_hits,
        "matched_specialties": sorted(set(matched_specialties)),
        "summary": "The symptom pattern most likely fits a primary care evaluation first.",
        "next_step": next_step,
    }

