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
    "ucla-daryl-lum": {
        "clinical_focus": [
            "Long-term adult primary care and annual wellness visits",
            "Cancer screening and preventive follow-up planning",
            "Medication review for patients managing multiple ongoing issues",
            "Continuity care within a large academic medical system",
        ],
        "care_approach": (
            "Dr. Lum is a steady, classic primary care fit for patients who want an experienced "
            "internist with a preventive mindset and a calm, structured visit style."
        ),
        "education": [
            "MD, Tufts University School of Medicine",
            "Residency, Internal Medicine, UCLA School of Medicine",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Strong fit for preventive primary care in Westwood",
            "Useful when the goal is long-term continuity rather than urgent triage",
            "Good option for screening-focused adult care",
        ],
        "accepts_new_patients": True,
    },
    "ucla-clifford-pang": {
        "clinical_focus": [
            "Family medicine for adults and broader household primary care",
            "Preventive care, mental health check-ins, and chronic condition review",
            "Mandarin-friendly visits for patients who value language support",
            "New-patient primary care when communication style matters",
        ],
        "care_approach": (
            "Dr. Pang is a strong fit when the user wants a family medicine physician who blends "
            "clear communication, preventive care, and a more personable first-visit experience."
        ),
        "education": [
            "DO, Philadelphia College of Osteopathic Medicine",
            "Residency, Family Medicine, Lankenau Hospital",
        ],
        "board_certifications": [
            "American Board of Family Medicine",
        ],
        "visit_highlights": [
            "Good match for Mandarin-speaking patients",
            "Accepting new patients with direct UCLA online booking",
            "Strong option for patients choosing between clinical fit and communication comfort",
        ],
        "accepts_new_patients": True,
    },
    "ucla-yatindra-patel": {
        "clinical_focus": [
            "Adult primary care with a newer but highly rated UCLA panel",
            "Thorough follow-up for new symptoms and medication questions",
            "Preventive visits with a collaborative, less rushed visit style",
            "Primary care for patients who want clear explanations and next steps",
        ],
        "care_approach": (
            "Dr. Patel is especially helpful for patients who want a newer primary care physician "
            "with strong patient feedback around listening carefully and working through options."
        ),
        "education": [
            "MD, Case Western Reserve University School of Medicine",
            "Residency, Internal Medicine, Cedars-Sinai Medical Center",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Accepting new patients in Westwood",
            "Good fit for thoughtful adult primary care",
            "Strong option when the user values a collaborative tone",
        ],
        "accepts_new_patients": True,
    },
    "ucla-patrick-yao": {
        "clinical_focus": [
            "High-continuity adult primary care and annual preventive visits",
            "Medication review, chronic disease follow-up, and longitudinal planning",
            "Mandarin-friendly primary care within UCLA Health",
            "Patients who want a highly reviewed, established PCP in Westwood",
        ],
        "care_approach": (
            "Dr. Yao is a reassuring choice when the user wants a very established internist with "
            "strong patient trust, clear communication, and long-term UCLA follow-through."
        ),
        "education": [
            "MD, UCLA School of Medicine",
            "Residency, Internal Medicine, UCLA School of Medicine",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Very high review volume among UCLA primary care options",
            "Mandarin language support",
            "Strong fit for users prioritizing trust and continuity",
        ],
        "accepts_new_patients": True,
    },
    "ucla-peter-young": {
        "clinical_focus": [
            "General primary care and complex care coordination",
            "Medication review and follow-up for patients with multiple conditions",
            "Preventive care that still accounts for higher-acuity medical histories",
            "Primary care for users who want a thoughtful, deeply engaged PCP",
        ],
        "care_approach": (
            "Dr. Young works especially well for patients who want a primary care doctor with "
            "more time-intensive follow-through, careful listening, and strong complex-care coordination."
        ),
        "education": [
            "MD, Columbia University College of Physicians and Surgeons",
            "Residency, Internal Medicine, Columbia University Medical Center",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Highly rated for empathy and thoroughness",
            "Good fit when the user wants more than a quick one-off visit",
            "Strong option for complex primary care handoffs in UCLA",
        ],
        "accepts_new_patients": True,
    },
    "ucla-sarah-takimoto": {
        "clinical_focus": [
            "Adult primary care and preventive follow-up in Santa Monica",
            "Medication review and longer-term care planning",
            "Users who want a newer PCP with strong visit feedback",
            "Primary care-first evaluation before escalating elsewhere",
        ],
        "care_approach": (
            "Dr. Takimoto is a strong fit when the user wants a warm but structured primary care "
            "visit that keeps the next steps clear without feeling rushed."
        ),
        "education": [
            "MD, UCSF School of Medicine",
            "Residency, Internal Medicine, UCLA Department of Internal Medicine",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Accepting new patients in Santa Monica",
            "Strong option for routine primary care and follow-up",
            "Good fit for users who want a balanced, supportive visit style",
        ],
        "accepts_new_patients": True,
    },
    "ucla-sarah-kim": {
        "clinical_focus": [
            "Adult primary care with extra depth around kidney and chronic care issues",
            "Detailed medication review and lab interpretation",
            "Users who want especially thorough explanations",
            "Longitudinal primary care in Santa Monica",
        ],
        "care_approach": (
            "Dr. Kim tends to fit patients who want a detailed, highly explanatory internist "
            "with strong continuity and a careful approach to workups."
        ),
        "education": [
            "MD, David Geffen School of Medicine at UCLA",
            "Residency, Internal Medicine, Olive View-UCLA Medical Center",
            "Fellowship, Nephrology, Cedars-Sinai Medical Center",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Very strong patient experience scores",
            "Good fit for users who want clear explanations and follow-through",
            "Useful when chronic disease management matters as much as acute symptoms",
        ],
        "accepts_new_patients": True,
    },
    "ucla-noah-ravenborg": {
        "clinical_focus": [
            "Preventive adult primary care and routine wellness visits",
            "LGBTQ+ health, HIV prevention, and inclusive primary care",
            "Primary care for patients who value patient-centered decision making",
            "Follow-up planning for recurring or longer-running symptoms",
        ],
        "care_approach": (
            "Dr. Ravenborg is a strong fit when the user wants an inclusive, patient-centered "
            "internist who is known for being thorough, thoughtful, and prevention-oriented."
        ),
        "education": [
            "MD, George Washington University School of Medicine",
            "Residency, Internal Medicine, UCLA School of Medicine",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
            "Certified HIV Specialist, American Academy of HIV Medicine",
        ],
        "visit_highlights": [
            "Strong preventive care orientation",
            "Good fit for users who want an especially collaborative tone",
            "Useful when inclusive primary care is a top priority",
        ],
        "accepts_new_patients": True,
    },
    "ucla-jeffrey-fujimoto": {
        "clinical_focus": [
            "Adult primary care with sports medicine crossover",
            "Preventive care and recovery planning for active patients",
            "Primary care for musculoskeletal questions that still need a PCP lens",
            "General outpatient care in Santa Monica",
        ],
        "care_approach": (
            "Dr. Fujimoto is a strong fit for patients who want traditional primary care plus "
            "a sports-medicine-informed perspective when activity, mobility, or training matter."
        ),
        "education": [
            "MD, David Geffen School of Medicine at UCLA",
            "Residency, Internal Medicine, UCLA School of Medicine",
            "Fellowship, Sports Medicine, Cedars-Sinai Kerlan-Jobe",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Good fit for active patients managing both primary care and mobility concerns",
            "Strong option in Santa Monica with official UCLA booking access",
            "Useful when sports or exercise context matters to the visit",
        ],
        "accepts_new_patients": True,
    },
    "keck-ron-ben-ari": {
        "clinical_focus": [
            "Adult primary care, preventive care, and continuity visits",
            "Medication review for blood pressure, cholesterol, and diabetes",
            "Primary care follow-up on the USC Health Sciences Campus",
            "Care for patients who want an experienced teaching physician",
        ],
        "care_approach": (
            "Dr. Ben-Ari is a steady, teaching-oriented internist who fits users looking "
            "for a classic primary care physician with a long-standing USC clinical practice."
        ),
        "education": [
            "MD, Keck School of Medicine of USC",
            "Residency, Internal Medicine, USC Internal Medicine Residency Program",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Strong fit for continuity-oriented adult primary care",
            "Good option when the user values teaching-hospital depth and clinical experience",
            "Helpful for preventive visits and longer-term management planning",
        ],
        "accepts_new_patients": True,
    },
    "keck-nida-hamiduzzaman": {
        "clinical_focus": [
            "Adult primary care and chronic disease management",
            "Population-health-informed primary care follow-up",
            "Medication review and preventive care planning",
            "Primary care visits with Urdu language access",
        ],
        "care_approach": (
            "Dr. Hamiduzzaman is a strong fit for patients who want compassionate, "
            "values-aware primary care with attention to chronic condition follow-through."
        ),
        "education": [
            "MD, American University of the Caribbean",
            "Residency, Internal Medicine, University of Oklahoma",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Useful when continuity and chronic disease follow-up matter",
            "Urdu language access can make first visits easier for some families",
            "Good option for USC-area patients who want a Keck primary care entry point",
        ],
        "accepts_new_patients": True,
    },
    "keck-joshua-sapkin": {
        "clinical_focus": [
            "Preventive adult primary care and routine wellness visits",
            "Hypertension, diabetes, and cholesterol management",
            "Primary care visits in both eastside and downtown Los Angeles",
            "Care planning for users who want more lifestyle-based coaching",
        ],
        "care_approach": (
            "Dr. Sapkin emphasizes patient education and practical goal setting, which "
            "makes him a good fit when the user wants a collaborative primary care relationship."
        ),
        "education": [
            "MD, Keck School of Medicine of USC",
            "Residency, Internal Medicine, LAC + USC Medical Center",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
        ],
        "visit_highlights": [
            "Good fit for users who value explanation and prevention",
            "Downtown clinic access is convenient for many central Los Angeles users",
            "Helpful when the user wants a physician comfortable with long-term condition management",
        ],
        "accepts_new_patients": True,
    },
    "keck-maria-gorgona": {
        "clinical_focus": [
            "Adult primary care with strong preventive care foundations",
            "Hypertension, diabetes, lipid disorders, and thyroid follow-up",
            "HIV prevention, diagnosis, and treatment support",
            "Downtown Los Angeles primary care with culturally sensitive communication",
        ],
        "care_approach": (
            "Dr. Gorgona is a strong fit for users who want compassionate adult primary care "
            "with additional HIV medicine expertise and a relationship-centered visit style."
        ),
        "education": [
            "MD, University of Santo Tomas",
            "Residency, Internal Medicine, City Hospital Center at Elmhurst",
        ],
        "board_certifications": [
            "American Board of Internal Medicine",
            "Credentialed specialist in HIV medicine",
        ],
        "visit_highlights": [
            "Useful when the user wants both general primary care and HIV-focused experience",
            "Strong downtown Los Angeles option with Tagalog language access",
            "Good fit for patients who want a culturally sensitive, nonjudgmental tone",
        ],
        "accepts_new_patients": True,
    },
    "keck-caitlin-mcauley": {
        "clinical_focus": [
            "Family medicine and preventive primary care",
            "Gender-affirming care, HIV/PrEP, and routine women's health",
            "Mental health, sleep, and musculoskeletal questions in primary care",
            "Downtown Los Angeles primary care with telemedicine availability",
        ],
        "care_approach": (
            "Dr. McAuley takes a whole-person family medicine approach, which makes her a "
            "strong fit for users who want broad, inclusive primary care rather than a narrow specialty visit."
        ),
        "education": [
            "DO, Touro University College of Osteopathic Medicine",
            "Residency, Family Medicine, Chino Valley Medical Center",
        ],
        "board_certifications": [
            "Family medicine training",
        ],
        "visit_highlights": [
            "Strong choice for inclusive first-step primary care",
            "Good fit for users looking for preventive care, PrEP, or gender-affirming care context",
            "Downtown location can be especially convenient from USC and central Los Angeles",
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
