"use client";

import Link from "next/link";
import { AuthStatus } from "@/components/AuthStatus";
import { useTranslation } from "@/lib/LanguageProvider";

export default function LayoutContent({
  children,
}:{
  children:React.ReactNode;
}){
  const {t,lang,setLang}=useTranslation();

  const navItems=[
    {href:"/",label:t.nav_overview},
    {href:"/symptom",label:t.nav_symptoms},
    {href:"/insurance",label:t.nav_insurance},
    {href:"/doctors",label:t.nav_doctors},
    {href:"/booking",label:t.nav_booking},
  ];

  return(
    <div className="site-shell">
      <header className="topbar">
        <Link className="brand" href="/">
          <span>AI Healthcare Assistant</span>
          <small>Symptom to booking navigation</small>
        </Link>

        <div className="topbar-controls">

          <nav className="topnav">
            {navItems.map((item)=>(
              <Link href={item.href} key={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>

          {/* language switch */}
          <select
            value={lang}
            onChange={(e)=>setLang(e.target.value as any)}
          >
            <option value="English">EN</option>
            <option value="Mandarin">中</option>
            <option value="Spanish">ES</option>
          </select>

          <AuthStatus />
        </div>
      </header>

      {children}
    </div>
  );
}