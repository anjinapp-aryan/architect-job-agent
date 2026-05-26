const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: { "content-type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export type Job = {
  id: number;
  title: string;
  company_name: string;
  country?: string;
  location?: string;
  source: string;
  url?: string;
  match_score?: number;
  recommendation?: string;
};

export type Application = {
  id: number;
  job_id: number;
  status: string;
  notes?: string;
  updated_at: string;
};
