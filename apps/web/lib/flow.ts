import type { FlowState } from "@/lib/types";
import { getAuthSession } from "@/lib/auth";

const FLOW_STORAGE_KEY = "ai-healthcare-assistant-flow";

function getScopedFlowStorageKey(): string {
  const session = getAuthSession();
  return session?.user?.id ? `${FLOW_STORAGE_KEY}:${session.user.id}` : FLOW_STORAGE_KEY;
}

export function getFlowState(): FlowState {
  if (typeof window === "undefined") {
    return {};
  }

  const raw = window.sessionStorage.getItem(getScopedFlowStorageKey());
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as FlowState;
  } catch {
    return {};
  }
}

export function setFlowState(next: FlowState): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(getScopedFlowStorageKey(), JSON.stringify(next));
}

export function patchFlowState(patch: Partial<FlowState>): FlowState {
  const next = { ...getFlowState(), ...patch };
  setFlowState(next);
  return next;
}
