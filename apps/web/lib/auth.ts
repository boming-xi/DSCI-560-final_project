import type { AuthenticatedUser } from "@/lib/types";

export type AuthSession = {
  access_token: string;
  token_type: string;
  user: AuthenticatedUser;
};

const AUTH_STORAGE_KEY = "ai-healthcare-assistant-auth";

export function getAuthSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function saveAuthSession(session: AuthSession): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  emitAuthChange();
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  emitAuthChange();
}

export function emitAuthChange(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event("auth-changed"));
}

export function getAccessToken(): string | null {
  return getAuthSession()?.access_token ?? null;
}
