from __future__ import annotations

from app.models.doctor import DoctorRecord

DoctorDetailContent = dict[str, object]

DOCTOR_DETAIL_LIBRARY: dict[str, DoctorDetailContent] = {
    "dr-michelle-lin": {
        "clinical_focus": [
            "Sore throat, fever, and upper respiratory infections",
            "New patient primary care for students and recent arrivals",
            "Digestive symptoms, hydration issues, and follow-up visits",
            "Routine preventive care and vaccine planning",
        ],
        "care_approach": (
            "Dr. Lin is known for calm, structured visits that help patients understand "
            "what is most urgent now versus what can be safely monitored at home."
        ),
        "education": [
            "MD, University of California, San Diego School of Medicine",
            "Residency, Family Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Family Medicine",
            "Telehealth care delivery certificate",
        ],
        "visit_highlights": [
            "Explains likely next steps in plain language",
            "Comfortable working with international students",
            "Good fit for first-visit triage and follow-up planning",
        ],
        "accepts_new_patients": True,
    },
    "dr-daniel-park": {
        "clinical_focus": [
            "Same-day respiratory and flu-like symptoms",
            "Minor injuries, sprains, and urgent work or school notes",
            "Rapid symptom worsening that does not yet require an ER",
            "Evening and weekend urgent care needs",
        ],
        "care_approach": (
            "Dr. Park tends to be direct and efficiency-focused, which works well for "
            "patients who need fast decisions, testing, and treatment escalation guidance."
        ),
        "education": [
            "MD, Keck School of Medicine of USC",
            "Residency, Emergency and Urgent Care Track, Cedars-Sinai",
        ],
        "board_certifications": [
            "American Board of Family Medicine",
            "Urgent care clinical procedures training",
        ],
        "visit_highlights": [
            "Best option when timing matters more than continuity",
            "Strong for after-hours access",
            "Often able to start workups immediately",
        ],
        "accepts_new_patients": True,
    },
    "dr-sophia-ramirez": {
        "clinical_focus": [
            "Adult primary care and longer-running symptoms",
            "Diagnostic workups for fatigue, fever, and lab abnormalities",
            "Medication review and chronic condition follow-up",
            "Preventive screening with detailed counseling",
        ],
        "care_approach": (
            "Dr. Ramirez is detail-oriented and especially helpful when patients want a "
            "careful explanation of why a workup is being recommended."
        ),
        "education": [
            "MD, Stanford School of Medicine",
            "Residency, Internal Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "High continuity for ongoing issues",
            "Strong for second opinions after urgent care",
            "Often praised for clear explanations and follow-through",
        ],
        "accepts_new_patients": True,
    },
    "dr-evelyn-cho": {
        "clinical_focus": [
            "Persistent sore throat and recurrent tonsil issues",
            "Sinus pain, congestion, and nasal breathing problems",
            "Voice changes and ENT-specific follow-up referrals",
            "Ear pain, pressure, and hearing-related concerns",
        ],
        "care_approach": (
            "Dr. Cho is specialty-focused and helpful once symptoms are clearly ENT-related "
            "or when a primary care clinician has recommended a referral."
        ),
        "education": [
            "MD, Northwestern University Feinberg School of Medicine",
            "Residency, Otolaryngology, UC Irvine Health",
        ],
        "board_certifications": [
            "American Board of Otolaryngology",
        ],
        "visit_highlights": [
            "Useful for referral-based specialist escalation",
            "Good Mandarin and Korean language access",
            "Often chosen for sinus and throat follow-up visits",
        ],
        "accepts_new_patients": False,
    },
    "dr-aarav-patel": {
        "clinical_focus": [
            "Rashes, eczema, and contact irritation",
            "Acne treatment planning and medication follow-up",
            "New skin changes that need specialist review",
            "Telehealth-friendly photo review follow-ups",
        ],
        "care_approach": (
            "Dr. Patel combines quick visual assessment with practical treatment plans, "
            "which makes him a good fit for common dermatology questions."
        ),
        "education": [
            "MD, Baylor College of Medicine",
            "Residency, Dermatology, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Dermatology",
        ],
        "visit_highlights": [
            "Strong telehealth option for visible skin concerns",
            "Good for structured treatment walkthroughs",
            "Best when a specialist consult is clearly needed",
        ],
        "accepts_new_patients": True,
    },
    "dr-hannah-kim": {
        "clinical_focus": [
            "Preventive OB-GYN visits and reproductive health questions",
            "Cycle-related symptoms and contraception counseling",
            "Follow-up after urgent symptoms are stabilized",
            "Continuity visits that need a specialist perspective",
        ],
        "care_approach": (
            "Dr. Kim focuses on steady, supportive follow-up and tends to spend extra time "
            "helping patients compare options before making decisions."
        ),
        "education": [
            "MD, Columbia University Vagelos College of Physicians and Surgeons",
            "Residency, Obstetrics and Gynecology, Kaiser Los Angeles",
        ],
        "board_certifications": [
            "American Board of Obstetrics and Gynecology",
        ],
        "visit_highlights": [
            "Good fit for preventive and follow-up visits",
            "Frequently recommended for careful counseling",
            "Works well when primary care hands off to specialty care",
        ],
        "accepts_new_patients": True,
    },
    "dr-miguel-torres": {
        "clinical_focus": [
            "Reflux, stomach pain, and ongoing digestive symptoms",
            "Specialist review after primary care or urgent care testing",
            "Persistent abdominal symptoms that need GI input",
            "Follow-up planning after lab or imaging abnormalities",
        ],
        "care_approach": (
            "Dr. Torres is methodical and tends to be most helpful when patients already "
            "have a symptom history or initial workup that needs specialist interpretation."
        ),
        "education": [
            "MD, University of Texas Southwestern Medical School",
            "Residency, Internal Medicine; Fellowship, Gastroenterology, Cedars-Sinai",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
            "Board Certified in Gastroenterology",
        ],
        "visit_highlights": [
            "Best after initial triage has narrowed the problem",
            "Helpful for persistent GI symptoms",
            "Often chosen for careful follow-up planning",
        ],
        "accepts_new_patients": False,
    },
    "dr-amy-sullivan": {
        "clinical_focus": [
            "Fast-access primary care for common illness visits",
            "Initial workups before deciding on specialist care",
            "School, work, and return-to-class clearance questions",
            "Short-notice telehealth or in-person follow-up",
        ],
        "care_approach": (
            "Dr. Sullivan is practical and access-oriented, which makes her a strong option "
            "when patients need a same-day starting point rather than a long specialist visit."
        ),
        "education": [
            "MD, University of Colorado School of Medicine",
            "Residency, Family Medicine, USC/LA General",
        ],
        "board_certifications": [
            "American Board of Family Medicine",
        ],
        "visit_highlights": [
            "Very fast access for first-step care",
            "Good for symptom triage and basic workups",
            "Strong telehealth availability for uncomplicated issues",
        ],
        "accepts_new_patients": True,
    },
    "ucla-kyung-ah-cho-anderson": {
        "clinical_focus": [
            "Adult primary care and annual preventive visits",
            "Ongoing care for diabetes, blood pressure, and cholesterol",
            "Medication review and follow-up after urgent visits",
            "Longitudinal care when patients want one central PCP",
        ],
        "care_approach": (
            "Dr. Cho Anderson is a continuity-focused UCLA primary care physician who fits "
            "patients looking for a steady long-term home base rather than a one-off urgent visit."
        ),
        "education": [
            "MD, David Geffen School of Medicine at UCLA",
            "Residency, Internal Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Strong fit for long-term adult primary care",
            "Good for patients who want a more relationship-based visit style",
            "Useful when the next step is establishing ongoing care in Los Angeles",
        ],
        "accepts_new_patients": True,
    },
    "ucla-su-hutchinson": {
        "clinical_focus": [
            "Adult wellness visits and preventive screenings",
            "Primary care follow-up after same-day or urgent symptoms",
            "Medication management and chronic condition review",
            "Care coordination across specialist referrals",
        ],
        "care_approach": (
            "Dr. Hutchinson combines preventive care with structured follow-through, which makes "
            "her a strong option for patients who want both primary care and referral coordination."
        ),
        "education": [
            "MD, University of California medical training",
            "Residency, Internal Medicine, UCLA-affiliated training",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Well suited for preventive and continuity visits",
            "Helpful when the user wants a clear PCP before seeing multiple specialists",
            "Often a good bridge between acute concerns and longer-term management",
        ],
        "accepts_new_patients": True,
    },
    "ucla-daniel-pourshalimi": {
        "clinical_focus": [
            "General internal medicine and adult symptom follow-up",
            "Workups that need a careful PCP before specialist escalation",
            "Chronic condition management and care-plan refinement",
            "Primary care for patients transitioning into a new health system",
        ],
        "care_approach": (
            "Dr. Pourshalimi is a good fit when the user wants a high-trust internist who can "
            "translate symptoms into a structured workup and coordinate the next referrals."
        ),
        "education": [
            "MD, UCLA-affiliated medical training",
            "Residency, Internal Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Strong option for thoughtful adult primary care",
            "Good for patients who want to slow down and compare options before deciding",
            "Useful for longer symptom stories that need interpretation",
        ],
        "accepts_new_patients": True,
    },
    "ucla-sandra-vizireanu": {
        "clinical_focus": [
            "Complex adult primary care and preventive follow-up",
            "Medication counseling and longitudinal symptom tracking",
            "Care transitions after urgent care or outside consultations",
            "General internal medicine for new Los Angeles patients",
        ],
        "care_approach": (
            "Dr. Vizireanu is especially helpful for patients who need a clear explanation of "
            "tradeoffs and a consistent primary care clinician after an initial triage step."
        ),
        "education": [
            "MD, internal medicine training pathway",
            "Residency, Internal Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Good fit for patients seeking continuity after urgent care",
            "Often useful when care decisions feel fragmented",
            "Strong option for primary care in the UCLA Westside system",
        ],
        "accepts_new_patients": True,
    },
    "ucla-ryan-aronin": {
        "clinical_focus": [
            "Primary care and preventive medicine in a major academic system",
            "Adult wellness, screening, and medication review",
            "Continuity visits for recurring symptoms or chronic disease",
            "Care coordination for patients who may need future referrals",
        ],
        "care_approach": (
            "Dr. Aronin is a solid choice when the user wants a stable UCLA primary care entry "
            "point with strong institutional follow-up and easier handoffs to other specialists."
        ),
        "education": [
            "MD, academic internal medicine training",
            "Residency, Internal Medicine, UCLA Health",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Strong option for establishing primary care in Westwood",
            "Good for patients who expect to stay within one system",
            "Works well when future specialty referrals are likely",
        ],
        "accepts_new_patients": True,
    },
}

SPECIALTY_FALLBACKS: dict[str, DoctorDetailContent] = {
    "family medicine": {
        "clinical_focus": [
            "General primary care and first-visit symptom triage",
            "Follow-up after urgent care or specialist visits",
            "Preventive visits and routine care planning",
        ],
        "care_approach": "Balances immediate symptom relief with practical next-step planning.",
        "education": ["Board-certified clinician with primary care training"],
        "board_certifications": ["Primary care board certification"],
        "visit_highlights": [
            "Helpful for building a first care plan",
            "Strong continuity option after urgent symptoms settle",
        ],
        "accepts_new_patients": True,
    }
}


def get_doctor_detail_content(doctor: DoctorRecord) -> DoctorDetailContent:
    return DOCTOR_DETAIL_LIBRARY.get(
        doctor.id,
        SPECIALTY_FALLBACKS.get(doctor.specialty.lower(), {}),
    )
