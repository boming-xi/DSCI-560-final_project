"use client";

import { SymptomForm } from "@/components/SymptomForm";
import { useProtectedRoute } from "@/lib/useProtectedRoute";

export default function SymptomPage() {
  const { isCheckingAuth, session } = useProtectedRoute();

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">Preparing your symptom intake...</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <main className="page-shell">
      <SymptomForm />
    </main>
  );
}
