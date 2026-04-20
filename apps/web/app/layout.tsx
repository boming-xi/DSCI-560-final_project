import type { ReactNode } from "react";
import { LanguageProvider } from "@/lib/LanguageProvider";
import LayoutContent from "./LayoutContent";

import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata={
  title:"AI Healthcare Assistant",
  description:"Symptom triage, insurance guidance, doctor ranking, and official booking handoff.",
};

export default function RootLayout({
  children,
}:{
  children:ReactNode;
}){
  return(
    <html lang="en">
      <body>
        <LanguageProvider>
          <LayoutContent>{children}</LayoutContent>
        </LanguageProvider>
      </body>
    </html>
  );
}