"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getAuthSession } from "@/lib/auth";

const LOGIN_REDIRECT = "/login?next=%2Fsymptom";

type StartDemoLinkProps = {
  label?: string;
};

export function StartDemoLink({ label = "Begin guided care" }: StartDemoLinkProps) {
  const [href, setHref] = useState(LOGIN_REDIRECT);

  useEffect(() => {
    const nextHref = getAuthSession() ? "/symptom" : LOGIN_REDIRECT;
    setHref(nextHref);

    function syncHref() {
      setHref(getAuthSession() ? "/symptom" : LOGIN_REDIRECT);
    }

    window.addEventListener("auth-changed", syncHref);
    window.addEventListener("storage", syncHref);
    return () => {
      window.removeEventListener("auth-changed", syncHref);
      window.removeEventListener("storage", syncHref);
    };
  }, []);

  return (
    <Link className="button button-primary" href={href}>
      {label}
    </Link>
  );
}
