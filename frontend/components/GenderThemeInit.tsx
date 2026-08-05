"use client";

import { useEffect } from "react";
import { applyGenderTheme, getStoredGenderPreference } from "@/lib/genderTheme";

/** Applies the stored gender/theme preference to <html data-gender="…">
 * on every page load. Client-only (no SSR value) so there's a brief flash
 * of the neutral palette on first paint before this runs — acceptable
 * trade-off for not needing a cookie round-trip for a purely cosmetic
 * preference. */
export default function GenderThemeInit() {
  useEffect(() => {
    applyGenderTheme(getStoredGenderPreference());
  }, []);
  return null;
}
