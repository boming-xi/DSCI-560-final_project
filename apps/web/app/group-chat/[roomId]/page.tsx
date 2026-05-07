"use client";

import { PeerSupportChat } from "@/components/PeerSupportChat";
import { useProtectedRoute } from "@/lib/useProtectedRoute";
import { useTranslation } from "@/lib/LanguageProvider";

export default function GroupChatRoomPage({
  params,
}: {
  params: { roomId: string };
}) {
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

  return (
    <PeerSupportChat
      initialRoomId={decodeURIComponent(params.roomId)}
      roomOnly
    />
  );
}
