import { AuthForm } from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <main className="page-shell">
      <AuthForm mode="login" />
    </main>
  );
}

