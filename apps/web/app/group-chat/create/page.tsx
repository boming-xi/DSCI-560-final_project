"use client";

import { CreateSupportRoomForm } from "@/components/CreateSupportRoomForm";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import { useTranslation } from "@/lib/LanguageProvider";

export default function CreateGroupChatRoomPage() {
  const { t } = useTranslation();
  const { isCheckingAuth, session } = useProtectedRoute();

  if (isCheckingAuth) {
    return (
      <main className="page-shell">
        <div className="panel">{t.community.authLoading}</div>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  return <CreateSupportRoomForm />;
}
