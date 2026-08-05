export type GenderPreference = "male" | "female" | "other";

const KEY = "whereto_gender_preference";

export function getStoredGenderPreference(): GenderPreference | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(KEY);
  return raw === "male" || raw === "female" || raw === "other" ? raw : null;
}

export function applyGenderTheme(pref: GenderPreference | null): void {
  if (typeof document === "undefined") return;
  if (pref) {
    document.documentElement.setAttribute("data-gender", pref);
  } else {
    document.documentElement.removeAttribute("data-gender");
  }
}

export function storeGenderPreference(pref: GenderPreference): void {
  localStorage.setItem(KEY, pref);
  applyGenderTheme(pref);
}

export function clearGenderPreference(): void {
  localStorage.removeItem(KEY);
  applyGenderTheme(null);
}
