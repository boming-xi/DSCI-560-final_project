import { Suspense } from "react";

import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <main className="page-shell">
      <Suspense fallback={<div className="panel">Loading login...</div>}>
        <AuthForm mode="login" />
      </Suspense>
    </main>
  );
}
