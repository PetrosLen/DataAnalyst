import { basicAuthHeader, type AdminCredentials } from "@/lib/adminAuth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class AdminAuthError extends Error {
  constructor() {
    super("Μη έγκυρα στοιχεία σύνδεσης");
  }
}

export type AdminVenueListItem = {
  id: number;
  slug: string;
  name: string;
  status: string;
  overall_confidence: number;
  primary_category_slug: string | null;
  city_area_slug: string | null;
  created_at: string;
};

export type AdminVenueTag = { slug: string; name: string; confidence: number };
export type AdminVenueSource = {
  id: number;
  source_type: string;
  source_ref: string | null;
  reliability_score: number;
  last_checked_at: string | null;
};

export type AdminVenueDetail = AdminVenueListItem & {
  description_short: string | null;
  description_long: string | null;
  address: string | null;
  phone: string | null;
  website: string | null;
  instagram_url: string | null;
  price_level: number | null;
  last_verified_at: string | null;
  tags: AdminVenueTag[];
  sources: AdminVenueSource[];
};

export type AdminVenueUpdate = Partial<{
  name: string;
  description_short: string;
  description_long: string;
  address: string;
  phone: string;
  website: string;
  instagram_url: string;
  price_level: number;
  status: string;
  overall_confidence: number;
}>;

async function adminFetch(
  path: string,
  creds: AdminCredentials,
  init?: RequestInit
): Promise<Response> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
      Authorization: basicAuthHeader(creds.email, creds.password),
    },
    cache: "no-store",
  });
  if (res.status === 401) throw new AdminAuthError();
  if (!res.ok) throw new Error(`Admin API error: ${res.status}`);
  return res;
}

export async function verifyCredentials(creds: AdminCredentials): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/admin/me`, {
    headers: { Authorization: basicAuthHeader(creds.email, creds.password) },
    cache: "no-store",
  });
  return res.ok;
}

export async function listVenues(
  creds: AdminCredentials,
  status?: string
): Promise<{ items: AdminVenueListItem[]; total: number }> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  const res = await adminFetch(`/admin/venues${qs}`, creds, undefined);
  return res.json();
}

export async function getVenue(creds: AdminCredentials, id: number): Promise<AdminVenueDetail> {
  const res = await adminFetch(`/admin/venues/${id}`, creds, undefined);
  return res.json();
}

export async function updateVenue(
  creds: AdminCredentials,
  id: number,
  update: AdminVenueUpdate
): Promise<AdminVenueDetail> {
  const res = await adminFetch(`/admin/venues/${id}`, creds, {
    method: "PATCH",
    body: JSON.stringify(update),
  });
  return res.json();
}
