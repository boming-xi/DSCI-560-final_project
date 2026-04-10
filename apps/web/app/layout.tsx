import type { ReactNode } from "react";
import Link from "next/link";

import { AuthStatus } from "@/components/AuthStatus";
import "./globals.css";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/symptom", label: "Symptoms" },
  { href: "/insurance", label: "Insurance" },
  { href: "/doctors", label: "Doctors" },
  { href: "/booking", label: "Booking" },
  { href: "/chat", label: "Chat" },
];

export const metadata = {
  title: "AI Healthcare Assistant",
  description: "Symptom triage, insurance matching, doctor ranking, and booking support.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="site-shell">
          <header className="topbar">
            <Link className="brand" href="/">
              <span>AI Healthcare Assistant</span>
              <small>Symptom to booking demo</small>
            </Link>
            <div className="topbar-controls">
              <nav className="topnav">
                {navItems.map((item) => (
                  <Link href={item.href} key={item.href}>
                    {item.label}
                  </Link>
                ))}
              </nav>
              <AuthStatus />
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
