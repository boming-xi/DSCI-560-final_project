"use client";

import { patchFlowState } from "@/lib/flow";
import type { DoctorProfile } from "@/lib/types";

type BeginDoctorBookingOptions = {
  onInternalBooking?: () => void;
};

export function beginDoctorBooking(
  doctor: DoctorProfile,
  options?: BeginDoctorBookingOptions,
): void {
  patchFlowState({ selectedDoctor: doctor });
  options?.onInternalBooking?.();
}
