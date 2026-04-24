import type {
  ReportResponse,
  MatchResponse,
  DogDetailResponse,
  DogsListResponse,
  InboxResponse,
  ThreadResponse,
} from "@/types";

// In Docker: VITE_API_BASE_URL is empty → relative /api (proxied by nginx)
// Locally:   VITE_API_BASE_URL=http://localhost:8000 → Vite dev proxy rewrites /api
const BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api`;

export async function reportDog(form: FormData): Promise<ReportResponse> {
  const res = await fetch(`${BASE}/report`, {
    method: "POST",
    body: form,
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function matchDog(form: FormData): Promise<MatchResponse> {
  const res = await fetch(`${BASE}/match`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDog(dogId: string): Promise<DogDetailResponse> {
  const res = await fetch(`${BASE}/dog/${dogId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listDogs(
  limit = 20,
  offset = 0,
  geoFilter?: { lat: number; lng: number; radiusKm: number },
): Promise<DogsListResponse> {
  let url = `${BASE}/dogs?limit=${limit}&offset=${offset}`;
  if (geoFilter) {
    url += `&lat=${geoFilter.lat}&lng=${geoFilter.lng}&radius_km=${geoFilter.radiusKm}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function identifyBreed(
  file: File,
): Promise<{ predictions: { breed: string; confidence: number }[] }> {
  const form = new FormData();
  form.append("image", file);
  const res = await fetch(`${BASE}/identify`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateDogStatus(
  dogId: string,
  status: "active" | "reunited",
): Promise<void> {
  const form = new FormData();
  form.append("status", status);
  const res = await fetch(`${BASE}/dog/${dogId}/status`, {
    method: "PATCH",
    body: form,
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function sendMessage(
  dogId: string,
  body: string,
): Promise<{ message_id: string; created_at: string }> {
  const form = new FormData();
  form.append("dog_id", dogId);
  form.append("body", body);
  const res = await fetch(`${BASE}/messages`, {
    method: "POST",
    body: form,
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getInbox(): Promise<InboxResponse> {
  const res = await fetch(`${BASE}/messages/inbox`, { credentials: "include" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getThread(dogId: string): Promise<ThreadResponse> {
  const res = await fetch(`${BASE}/messages/thread/${dogId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUnreadCount(): Promise<{ unread: number }> {
  const res = await fetch(`${BASE}/messages/unread-count`, {
    credentials: "include",
  });
  if (!res.ok) return { unread: 0 };
  return res.json();
}
