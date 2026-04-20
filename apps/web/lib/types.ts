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

export type InsuranceAdvisorProfile = {
  age?: number | null;
  state?: string | null;
  zip_code?: string | null;
  household_size?: number | null;
  income_band?: string | null;
  coverage_channel?: "student" | "marketplace" | "employer" | "unsure" | null;
  monthly_budget?: "low" | "medium" | "high" | null;
  care_usage?: "low" | "moderate" | "high" | null;
  referrals_ok?: boolean | null;
  keep_existing_doctors?: boolean | null;
  has_prescriptions?: boolean | null;
  preferred_language?: string | null;
};

export type InsuranceAdvisorSpeakerMessage = {
  speaker: "Navigator" | "Eligibility Checker" | "Plan Matcher";
  content: string;
};

export type InsuranceAdvisorRecommendation = {
  plan_id: string;
  doctor_search_plan_id?: string | null;
  provider: string;
  plan_name: string;
  plan_type: string;
  network_name?: string | null;
  metal_level?: string | null;
  insurance_query: string;
  fit_score: number;
  confidence_label: "early" | "good" | "strong";
  monthly_premium_band: "low" | "medium" | "high";
  monthly_premium_amount?: number | null;
  deductible_band: "low" | "medium" | "high";
  deductible_amount?: number | null;
  out_of_pocket_max_amount?: number | null;
  network_flexibility: "low" | "high";
  quality_rating?: number | null;
  advisor_blurb: string;
  reasons: string[];
  tradeoffs: string[];
  ideal_for: string[];
  purchase_url?: string | null;
  purchase_cta_label?: string | null;
  source_url?: string | null;
  network_url?: string | null;
  insurance_summary: InsuranceSummary;
};

export type InsuranceVerification = {
  status: "verified" | "likely" | "uncertain";
  label: string;
  reason: string;
  evidence: string[];
  network_name?: string | null;
  network_url?: string | null;
  source?: string | null;
};

export type InsuranceAdvisorResponse = {
  profile: InsuranceAdvisorProfile;
  profile_summary: string[];
  missing_fields: string[];
  readiness_label: "intake" | "narrowing" | "recommended";
  group_messages: InsuranceAdvisorSpeakerMessage[];
  recommendations: InsuranceAdvisorRecommendation[];
  suggested_prompts: string[];
  disclaimer: string;
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
  insurance_verification?: InsuranceVerification | null;
  ranking_breakdown?: RankingBreakdown | null;
  provider_system?: string | null;
  official_profile_url?: string | null;
  official_booking_url?: string | null;
  official_booking_label?: string | null;
  booking_system_name?: string | null;
  booking_note?: string | null;
  pilot_region?: string | null;
};

export type DoctorSearchResponse = {
  triage: TriageRecommendation;
  insurance_summary?: InsuranceSummary | null;
  doctors: DoctorProfile[];
  explanation: string[];
};

export type ChatTurn = {
  role: "user" | "assistant" | "system";
  content: string;
};

export type InsuranceAdvisorConversationTurn = {
  role: "user" | "assistant";
  speaker: string;
  content: string;
};

export type DoctorDecisionConversationTurn = {
  role: "user" | "assistant";
  speaker: string;
  content: string;
};

export type DoctorDecisionSpeakerMessage = {
  speaker: "Fit Analyst" | "Coverage Checker" | "Decision Guide";
  content: string;
};

export type DoctorDecisionSharedBrief = {
  shared_context_confirmed: boolean;
  case_summary: string;
  patient_goal: string;
  symptom_anchor?: string | null;
  insurance_anchor?: string | null;
  language_anchor?: string | null;
  priority_labels: string[];
  shortlist_names: string[];
  leading_doctor_name?: string | null;
  backup_doctor_name?: string | null;
  coverage_watchout?: string | null;
};

export type DoctorDecisionResponse = {
  group_messages: DoctorDecisionSpeakerMessage[];
  shared_brief?: DoctorDecisionSharedBrief | null;
  suggested_prompts: string[];
  recommended_doctor_id?: string | null;
  recommended_reason?: string | null;
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
  preferredLanguage?: string;
  location?: Location;
  triage?: TriageRecommendation;
  insuranceEntryMode?: "has_insurance" | "needs_help";
  insuranceQuery?: string;
  insuranceSummary?: InsuranceSummary;
  insuranceNetworkUrl?: string;
  insuranceAdvisorProfile?: InsuranceAdvisorProfile;
  insuranceAdvisorProfileSummary?: string[];
  insuranceAdvisorMissingFields?: string[];
  insuranceAdvisorReadinessLabel?: "intake" | "narrowing" | "recommended";
  insuranceAdvisorRecommendations?: InsuranceAdvisorRecommendation[];
  insuranceAdvisorConversation?: InsuranceAdvisorConversationTurn[];
  searchResult?: DoctorSearchResponse;
  doctorDecisionConversation?: DoctorDecisionConversationTurn[];
  doctorDecisionSuggestedPrompts?: string[];
  doctorDecisionRecommendedDoctorId?: string;
  doctorDecisionRecommendedReason?: string;
  doctorDecisionSharedBrief?: DoctorDecisionSharedBrief;
  doctorDecisionDoctorIdsSignature?: string;
  insurancePlanIdOverride?: string;
  insurancePurchaseUrl?: string;
  selectedDoctor?: DoctorProfile;
  documentTitle?: string;
  documentType?: string;
  documentText?: string;
  documentId?: string;
  documentFocusQuestion?: string;
};
