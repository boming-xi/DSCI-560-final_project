export type Location = {
  latitude: number;
  longitude: number;
};

export type TriageRecommendation = {
  urgency_level: "self-care" | "routine" | "soon" | "urgent" | "emergency";
  care_type: string;
  summary: string;
  red_flags: string[];
  next_step: string;
  safety_notice: string;
  matched_specialties: string[];
};

export type InsuranceSummary = {
  matched: boolean;
  plan_id?: string | null;
  provider?: string | null;
  plan_name?: string | null;
  plan_type?: string | null;
  referral_required_for_specialists: boolean;
  primary_care_copay?: number | null;
  specialist_copay?: number | null;
  urgent_care_copay?: number | null;
  notes: string[];
  match_confidence: number;
  normalized_query?: string | null;
};

export type RankingBreakdown = {
  specialty_score: number;
  insurance_score: number;
  distance_score: number;
  availability_score: number;
  language_score: number;
  trust_score: number;
  total_score: number;
  summary: string;
};

export type ClinicInfo = {
  id: string;
  name: string;
  care_types: string[];
  address: string;
  city: string;
  state: string;
  zip: string;
  phone: string;
  languages: string[];
  urgent_care: boolean;
  open_weekends: boolean;
};

export type DoctorProfile = {
  id: string;
  name: string;
  specialty: string;
  years_experience: number;
  languages: string[];
  rating: number;
  review_count: number;
  accepted_insurance: string[];
  availability_days: number;
  telehealth: boolean;
  gender: string;
  profile_blurb: string;
  appointment_modes: string[];
  accepts_new_patients: boolean;
  next_opening_label: string;
  clinical_focus: string[];
  care_approach: string;
  education: string[];
  board_certifications: string[];
  visit_highlights: string[];
  clinic: ClinicInfo;
  distance_km: number;
  estimated_cost?: number | null;
  referral_required: boolean;
  ranking_breakdown?: RankingBreakdown | null;
};

export type DoctorSearchResponse = {
  triage: TriageRecommendation;
  insurance_summary?: InsuranceSummary | null;
  doctors: DoctorProfile[];
  explanation: string[];
};

export type TimeSlot = {
  start: string;
  end: string;
  label: string;
  available: boolean;
};

export type BookingSlotsResponse = {
  doctor_id: string;
  doctor_name: string;
  slots: TimeSlot[];
};

export type BookingConfirmation = {
  confirmation_id: string;
  doctor_id: string;
  doctor_name: string;
  clinic_name: string;
  slot: string;
  estimated_cost?: number | null;
  next_steps: string[];
};

export type ChatTurn = {
  role: "user" | "assistant" | "system";
  content: string;
};

export type ChatResponse = {
  reply: string;
  cited_items: string[];
  suggested_next_actions: string[];
};

export type DocumentExplainResponse = {
  document_id: string;
  indexed_now: boolean;
  vector_store_backend: string;
  supporting_chunks: string[];
  summary: string;
  important_terms: string[];
  follow_up_questions: string[];
  disclaimer: string;
};

export type DocumentExtractResponse = {
  title: string;
  document_type: string;
  source_file_name: string;
  source_mime_type: string;
  extraction_method: string;
  extracted_text: string;
  extracted_preview: string;
  warnings: string[];
};

export type AuthenticatedUser = {
  id: string;
  name: string;
  email: string;
  role: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthenticatedUser;
};

export type FlowState = {
  symptomText?: string;
  durationDays?: number;
  preferredLanguage?: string;
  location?: Location;
  triage?: TriageRecommendation;
  insuranceQuery?: string;
  insuranceSummary?: InsuranceSummary;
  searchResult?: DoctorSearchResponse;
  selectedDoctor?: DoctorProfile;
  booking?: BookingConfirmation;
  documentTitle?: string;
  documentType?: string;
  documentText?: string;
  documentId?: string;
  documentFocusQuestion?: string;
};
