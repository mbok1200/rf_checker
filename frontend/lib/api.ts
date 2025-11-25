export type Health = { status: string; timestamp: string };

export function getApiKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('apiKey');
}
export function setApiKey(key: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('apiKey', key);
}
export function clearApiKey() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('apiKey');
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  const apiKey = getApiKey();
  if (apiKey) headers.set('X-API-Key', apiKey);
  const res = await fetch(`http://backend:8000${url}`, { ...options, headers });
  const text = await res.text();
  try {
    const data = text ? JSON.parse(text) : {};
    if (!res.ok) throw new Error((data as any).detail || text || res.statusText);
    return data as T;
  } catch (e) {
    if (!res.ok) throw new Error(text || res.statusText);
    throw e;
  }
}

export const api = {
  health: () => request<Health>('/health'),
  register: (username: string, password: string) =>
    request<{ message: string; username: string; api_key: string }>(
      '/api/auth/register',
      { method: 'POST', body: JSON.stringify({ username, password }) }
    ),
  login: (username: string, password: string) =>
    request<{ message: string; username: string; api_key: string }>(
      '/api/auth/login',
      { method: 'POST', body: JSON.stringify({ username, password }) }
    ),
  regenerateKey: (username: string, password: string) =>
    request<{ message: string; api_key: string }>(
      '/api/auth/regenerate-key',
      { method: 'POST', body: JSON.stringify({ username, password }) }
    ),
  check: (payload: { urls?: string[]; game_name?: string }) =>
    request<{ message: string; request_id: string; timestamp: string }>(
      '/api/check',
      { method: 'POST', body: JSON.stringify(payload) }
    ),
};
