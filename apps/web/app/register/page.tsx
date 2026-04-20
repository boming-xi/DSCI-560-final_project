import { Suspense } from "react";

import { AuthForm } from "@/components/AuthForm";

export default function RegisterPage() {
  return (
    <main className="page-shell">
      <Suspense fallback={<div className="panel">Preparing account setup...</div>}>
        <AuthForm mode="register" />
      </Suspense>
    </main>
  );
}
