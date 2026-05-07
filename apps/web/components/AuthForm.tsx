"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { api } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import { useTranslation } from "@/lib/LanguageProvider";
import type { AuthResponse } from "@/lib/types";

type AuthMode = "login" | "register";

type AuthFormProps = {
  mode: AuthMode;
};

export function AuthForm({ mode }: AuthFormProps) {
  const { t } = useTranslation();
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
          : t.auth.signInError
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
          : t.auth.quickAccessError
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="panel form-panel auth-form-panel" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <span className="eyebrow">
          {isRegister ? t.auth.registerEyebrow : t.auth.loginEyebrow}
        </span>
        <h1>{isRegister ? t.auth.registerTitle : t.auth.loginTitle}</h1>
        <p>
          {isRegister
            ? t.auth.registerSubtitle
            : t.auth.loginSubtitle}
        </p>
      </div>

      {isRegister ? (
        <label className="field">
          <span>{t.auth.name}</span>
          <input
            autoComplete="name"
            onChange={(event) => setName(event.target.value)}
            placeholder={t.auth.fullNamePlaceholder}
            value={name}
          />
        </label>
      ) : null}

      <label className="field">
        <span>{t.auth.email}</span>
        <input
          autoComplete="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder={t.auth.emailPlaceholder}
          type="email"
          value={email}
        />
      </label>

      <label className="field">
        <span>{t.auth.password}</span>
        <input
          autoComplete={isRegister ? "new-password" : "current-password"}
          onChange={(event) => setPassword(event.target.value)}
          placeholder={
            isRegister
              ? t.auth.registerPasswordPlaceholder
              : t.auth.loginPasswordPlaceholder
          }
          type="password"
          value={password}
        />
      </label>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="form-actions">
        <button className="button button-primary" disabled={isLoading} type="submit">
          {isLoading
            ? t.auth.submitting
            : isRegister
            ? t.auth.createAccount
            : t.auth.login}
        </button>
        {!isRegister ? (
          <button
            className="button button-secondary"
            disabled={isLoading}
            onClick={handleDemoLogin}
            type="button"
          >
            {t.auth.quickAccess}
          </button>
        ) : null}
      </div>

      <p className="auth-switch-copy">
        {isRegister ? t.auth.alreadyHaveAccount : t.auth.needAccount}{" "}
        <Link
          href={
            isRegister
              ? `/login${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`
              : `/register${nextPath ? `?next=${encodeURIComponent(nextPath)}` : ""}`
          }
        >
          {isRegister ? t.auth.logInHere : t.auth.registerHere}
        </Link>
      </p>
    </form>
  );
}
