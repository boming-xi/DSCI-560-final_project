import type {
  BookingConfirmation,
  BookingSlotsResponse,
  ChatResponse,
  ChatTurn,
  DoctorProfile,
  DoctorSearchResponse,
  DocumentExplainResponse,
  InsuranceSummary,
  Location,
  TriageRecommendation,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Request failed");
  }

  return (await response.json()) as T;
}

export const api = {
  triage: (payload: {
    symptom_text: string;
    duration_days: number;
    location: Location;
  }) =>
    request<TriageRecommendation>("/symptoms/triage", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  parseInsurance: (payload: {
    insurance_query?: string;
    uploaded_text?: string;
  }) =>
    request<InsuranceSummary>("/insurance/parse", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  searchDoctors: (payload: {
    symptom_text: string;
    insurance_query?: string;
    location: Location;
    preferred_language?: string;
    duration_days: number;
    top_k?: number;
  }) =>
    request<DoctorSearchResponse>("/doctors/search", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getDoctor: (doctorId: string) =>
    request<DoctorProfile>(`/doctors/${doctorId}`, { method: "GET" }),

  getBookingSlots: (doctorId: string) =>
    request<BookingSlotsResponse>(`/booking/slots/${doctorId}`, { method: "GET" }),

  createBooking: (payload: {
    doctor_id: string;
    patient_name: string;
    email: string;
    preferred_slot: string;
    insurance_plan_id?: string;
    symptom_text?: string;
    notes?: string;
  }) =>
    request<BookingConfirmation>("/booking/appointments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  sendChat: (payload: {
    message: string;
    conversation: ChatTurn[];
    symptom_text?: string;
    insurance_query?: string;
  }) =>
    request<ChatResponse>("/chat/message", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  explainDocument: (payload: {
    title?: string;
    content: string;
    document_type?: string;
  }) =>
    request<DocumentExplainResponse>("/documents/explain", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

