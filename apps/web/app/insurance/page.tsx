"use client";

import { InsuranceAdvisorChat } from "@/components/InsuranceAdvisorChat";
import { InsuranceUpload } from "@/components/InsuranceUpload";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function InsurancePage() {
  const { isCheckingAuth, session } = useProtectedRoute();

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Checking your account before opening insurance...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell">
      <div className="insurance-layout">
        <InsuranceAdvisorChat />
        <InsuranceUpload />
      </div>
    </main>
  );
}
