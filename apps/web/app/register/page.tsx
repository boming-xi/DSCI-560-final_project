import { Suspense } from "react";

import { AuthForm } from "@/components/AuthForm";

export default function RegisterPage() {
  return (
    <main className="page-shell">
      <Suspense fallback={<div className="panel" />}>
        <AuthForm mode="register" />
      </Suspense>
    </main>
  );
}
