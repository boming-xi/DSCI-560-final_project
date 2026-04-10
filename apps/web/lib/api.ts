import type {
  AuthResponse,
  AuthenticatedUser,
  BookingConfirmation,
  BookingSlotsResponse,
  ChatResponse,
  ChatTurn,
  DoctorProfile,
  DoctorSearchResponse,
  DocumentExtractResponse,
  DocumentExplainResponse,
  InsuranceSummary,
  Location,
  TriageRecommendation,
} from "@/lib/types";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function readErrorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail.trim()) {
        return payload.detail;
      }
    } catch {
      return "Request failed";
    }
  }

  const errorText = await response.text();
  return errorText || "Request failed";
}

async function request<T>(
  path: string,
  init: RequestInit,
  options?: { authRequired?: boolean },
): Promise<T> {
  const accessToken = options?.authRequired ? getAccessToken() : null;
  if (options?.authRequired && !accessToken) {
    throw new Error("Please log in to continue.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return (await response.json()) as T;
}

async function uploadRequest<T>(
  path: string,
  body: FormData,
  options?: { authRequired?: boolean },
): Promise<T> {
  const accessToken = options?.authRequired ? getAccessToken() : null;
  if (options?.authRequired && !accessToken) {
    throw new Error("Please log in to continue.");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body,
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
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
    request<BookingSlotsResponse>(
      `/booking/slots/${doctorId}`,
      { method: "GET" },
      { authRequired: true },
    ),

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
    }, { authRequired: true }),

  sendChat: (payload: {
    message: string;
    conversation: ChatTurn[];
    symptom_text?: string;
    insurance_query?: string;
  }) =>
    request<ChatResponse>("/chat/message", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { authRequired: true }),

  explainDocument: (payload: {
    title?: string;
    content?: string;
    document_type?: string;
    document_id?: string;
    focus_question?: string;
  }) =>
    request<DocumentExplainResponse>("/documents/explain", {
      method: "POST",
      body: JSON.stringify(payload),
    }, { authRequired: true }),

  extractDocument: (payload: {
    file: File;
    document_type?: string;
    title?: string;
  }) => {
    const formData = new FormData();
    formData.append("file", payload.file);
    if (payload.document_type) {
      formData.append("document_type", payload.document_type);
    }
    if (payload.title) {
      formData.append("title", payload.title);
    }

    return uploadRequest<DocumentExtractResponse>(
      "/documents/extract",
      formData,
      { authRequired: true },
    );
  },

  register: (payload: { name: string; email: string; password: string }) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  demoLogin: () =>
    request<AuthResponse>("/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  getMe: (accessToken: string) =>
    request<AuthenticatedUser>("/auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }),
};
