const KEY = "whereto_admin_credentials";

export type AdminCredentials = { email: string; password: string };

export function getStoredCredentials(): AdminCredentials | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AdminCredentials;
  } catch {
    return null;
  }
}

export function storeCredentials(creds: AdminCredentials): void {
  sessionStorage.setItem(KEY, JSON.stringify(creds));
}

export function clearCredentials(): void {
  sessionStorage.removeItem(KEY);
}

export function basicAuthHeader(email: string, password: string): string {
  return "Basic " + btoa(`${email}:${password}`);
}
