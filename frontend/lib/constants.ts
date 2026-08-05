export const DEFAULT_LOCATION = {
  // Πλατεία Αριστοτέλους, Θεσσαλονίκη — fallback όταν δεν δίνεται geolocation
  lat: 40.6328,
  lon: 22.9394,
};

export const INTENTS = [
  { slug: "bar", label: "Ήσυχο ποτό", emoji: "🍸" },
  { slug: "cafe", label: "Καφές / Δουλειά", emoji: "☕" },
  { slug: "restaurant", label: "Φαγητό / Date", emoji: "🍽️" },
  { slug: "wine_bar", label: "Wine bar", emoji: "🍷" },
] as const;

export const MOBILITY_OPTIONS = [
  { value: "walk", label: "Με τα πόδια" },
  { value: "transit", label: "ΜΜΜ" },
  { value: "car", label: "Αυτοκίνητο" },
] as const;

export const BUDGET_OPTIONS = [
  { value: 1, label: "€" },
  { value: 2, label: "€€" },
  { value: 3, label: "€€€" },
  { value: 4, label: "€€€€" },
] as const;
