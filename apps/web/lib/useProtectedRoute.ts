"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import {
  clearAuthSession,
  getAuthSession,
  saveAuthSession,
  type AuthSession,
} from "@/lib/auth";

export function useProtectedRoute() {
  const pathname = usePathname();
  const router = useRouter();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [session, setSession] = useState<AuthSession | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function ensureAuth() {
      const storedSession = getAuthSession();
      if (!storedSession) {
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
        if (isMounted) {
          setSession(null);
          setIsCheckingAuth(false);
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
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
        if (isMounted) {
          setSession(null);
        }
      } finally {
        if (isMounted) {
          setIsCheckingAuth(false);
        }
      }
    }

    void ensureAuth();
    return () => {
      isMounted = false;
    };
  }, [pathname, router]);

  return { isCheckingAuth, session };
}

