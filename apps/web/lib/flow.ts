import type { FlowState } from "@/lib/types";

const FLOW_STORAGE_KEY = "ai-healthcare-assistant-flow";

export function getFlowState(): FlowState {
  if (typeof window === "undefined") {
    return {};
  }

  const raw = window.sessionStorage.getItem(FLOW_STORAGE_KEY);
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

  window.sessionStorage.setItem(FLOW_STORAGE_KEY, JSON.stringify(next));
}

export function patchFlowState(patch: Partial<FlowState>): FlowState {
  const next = { ...getFlowState(), ...patch };
  setFlowState(next);
  return next;
}

