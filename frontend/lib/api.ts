const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type OpenStatus = "open" | "closed" | "unknown";

export type ScoreBreakdown = {
  intent: number;
  distance: number;
  open_now: number;
  budget: number;
  vibe: number;
  context: number;
  confidence_multiplier: number;
  total: number;
};

export type VenueRecommendation = {
  slug: string;
  name: string;
  description_short: string | null;
  distance_km: number;
  open_status: OpenStatus;
  price_level: number | null;
  overall_confidence: number;
  score: number;
  score_breakdown: ScoreBreakdown;
};

export type SearchResponse = {
  results: VenueRecommendation[];
  relaxed: boolean;
  relax_level: number;
  search_log_id: number;
};

export type Mobility = "walk" | "transit" | "car";

export type SearchRequestBody = {
  session_id: string;
  lat: number;
  lon: number;
  intent_category_slug: string;
  mobility?: Mobility;
  budget_min_level?: number | null;
  budget_max_level?: number | null;
  preferred_tag_slugs?: string[];
  limit?: number;
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function search(body: SearchRequestBody): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new ApiError(res.status, detail || `Search failed: ${res.status}`);
  }
  return res.json();
}

export type VenueTag = {
  slug: string;
  name: string;
  confidence: number;
};

export type VenueDetail = {
  slug: string;
  name: string;
  description_short: string | null;
  description_long: string | null;
  address: string | null;
  phone: string | null;
  website: string | null;
  instagram_url: string | null;
  price_level: number | null;
  primary_category_slug: string | null;
  overall_confidence: number;
  tags: VenueTag[];
  photo_urls: string[];
};

export async function getVenue(slug: string): Promise<VenueDetail | null> {
  const res = await fetch(`${API_BASE_URL}/venues/${encodeURIComponent(slug)}`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new ApiError(res.status, `Venue fetch failed: ${res.status}`);
  }
  return res.json();
}

export type FeedbackType = "thumbs_up" | "thumbs_down" | "closed" | "wrong_info" | "love_it";

export async function submitFeedback(params: {
  sessionId: string;
  venueSlug: string;
  feedbackType: FeedbackType;
  freeText?: string;
}): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: params.sessionId,
      venue_slug: params.venueSlug,
      feedback_type: params.feedbackType,
      free_text: params.freeText,
    }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(res.status, `Feedback failed: ${res.status}`);
  }
}
