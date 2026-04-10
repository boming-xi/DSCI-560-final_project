"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { clearAuthSession, getAuthSession, saveAuthSession } from "@/lib/auth";
import type { AuthSession } from "@/lib/auth";

export function AuthStatus() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const storedSession = getAuthSession();
      if (!storedSession) {
        if (isMounted) {
          setSession(null);
          setIsReady(true);
        }
        return;
      }

      try {
        const currentUser = await api.getMe(storedSession.access_token);
        const nextSession = { ...storedSession, user: currentUser };
        saveAuthSession(nextSession);
        if (isMounted) {
          setSession(nextSession);
        }
      } catch {
        clearAuthSession();
        if (isMounted) {
          setSession(null);
        }
      } finally {
        if (isMounted) {
          setIsReady(true);
        }
      }
    }

    function syncSessionFromStorage() {
      if (!isMounted) {
        return;
      }
      setSession(getAuthSession());
    }

    void restoreSession();
    window.addEventListener("auth-changed", syncSessionFromStorage);
    window.addEventListener("storage", syncSessionFromStorage);
    return () => {
      isMounted = false;
      window.removeEventListener("auth-changed", syncSessionFromStorage);
      window.removeEventListener("storage", syncSessionFromStorage);
    };
  }, []);

  if (!isReady) {
    return <div className="auth-shell auth-loading">Checking account...</div>;
  }

  if (!session) {
    return (
      <div className="auth-shell">
        <Link className="button button-secondary" href="/login">
          Log in
        </Link>
        <Link className="button button-primary" href="/register">
          Register
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-shell auth-signed-in">
      <div className="auth-user-copy">
        <strong>{session.user.name}</strong>
        <span>{session.user.email}</span>
      </div>
      <button
        className="button button-secondary"
        onClick={() => {
          clearAuthSession();
          setSession(null);
        }}
        type="button"
      >
        Log out
      </button>
    </div>
  );
}

