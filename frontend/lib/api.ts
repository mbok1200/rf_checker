export type Health = { status: string; timestamp: string };
const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === 'undefined' ? 'http://rf_checker_backend_1:8000' : 'https://ai_app.workerinua.fun');
console.log(PUBLIC_API_URL)
export function getApiKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('apiKey');
}
export function setApiKey(key: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('apiKey', key);
}
export function setUserId(key: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('userId', key);
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
  const res = await fetch(`${PUBLIC_API_URL}${url}`, { ...options, headers });
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
    request<{ message: string; username: string; user_id: string; api_key: string }>(
      '/api/auth/register',
      { method: 'POST', body: JSON.stringify({ username, password }) }
    ),
  login: (username: string, password: string) =>
    request<{ message: string; username: string; user_id: string; api_key: string }>(
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
