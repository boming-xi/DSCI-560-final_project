"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { api } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import type { AuthResponse } from "@/lib/types";

type AuthMode = "login" | "register";

type AuthFormProps = {
  mode: AuthMode;
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const isRegister = mode === "register";
  const nextPath = searchParams.get("next") || "/symptom";

  async function persistSession(authResponse: AuthResponse) {
    saveAuthSession({
      access_token: authResponse.access_token,
      token_type: authResponse.token_type,
      user: authResponse.user,
    });
    router.push(nextPath);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = isRegister
        ? await api.register({ name, email, password })
        : await api.login({ email, password });
      await persistSession(response);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "We could not complete sign-in right now."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDemoLogin() {
    setError("");
    setIsLoading(true);
    try {
      const response = await api.demoLogin();
      await persistSession(response);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Quick access sign-in is not available right now."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="panel form-panel auth-form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">{isRegister ? "Register" : "Log in"}</span>
        <h1>{isRegister ? "Create your account" : "Welcome back"}</h1>
        <p>
          {isRegister
            ? "Register once and your password will keep working on your next visit."
            : "Log in with your saved account or use the quick access login."}
        </p>
      </div>

      {isRegister ? (
        <label className="field">
          <span>Name</span>
          <input
            autoComplete="name"
            onChange={(event) => setName(event.target.value)}
            placeholder="Enter your full name"
            value={name}
          />
        </label>
      ) : null}

      <label className="field">
        <span>Email</span>
        <input
          autoComplete="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Enter your email address"
          type="email"
          value={email}
        />
      </label>

      <label className="field">
        <span>Password</span>
        <input
          autoComplete={isRegister ? "new-password" : "current-password"}
          onChange={(event) => setPassword(event.target.value)}
          placeholder={isRegister ? "Create a password with at least 6 characters" : "Enter your password"}
          type="password"
          value={password}
        />
      </label>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="form-actions">
        <button className="button button-primary" disabled={isLoading} type="submit">
          {isLoading ? "Submitting..." : isRegister ? "Create account" : "Log in"}
        </button>
        {!isRegister ? (
          <button
            className="button button-secondary"
            disabled={isLoading}
            onClick={handleDemoLogin}
            type="button"
          >
            Use quick access login
          </button>
        ) : null}
      </div>

      <p className="auth-switch-copy">
        {isRegister ? "Already have an account?" : "Need an account?"}{" "}
        <Link
          href={
            isRegister
              ? `/login${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`
              : `/register${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`
          }
        >
          {isRegister ? "Log in here" : "Register here"}
        </Link>
      </p>
    </form>
  );
}
