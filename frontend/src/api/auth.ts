import { loadSettings } from '../config'

export type AccountRole = 'admin' | 'operator' | 'viewer'
export interface SentinelUser {
  id: string
  email: string
  display_name: string
  role: AccountRole
  is_active: boolean
  created_at?: string | null
}
export interface AuthResponse extends SentinelUser { csrf_token: string }
export interface AccountCreate {
  email: string
  password: string
  display_name: string
  role: AccountRole
}
export interface AccountPatch {
  display_name?: string
  role?: AccountRole
  is_active?: boolean
}

let csrfToken = ''

export function getCsrfToken() {
  return csrfToken
}

function authUrl(path: string) {
  return loadSettings().apiBaseUrl.replace(/\/$/, '') + path
}

async function authRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers: Record<string, string> = {
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...(method !== 'GET' && method !== 'HEAD' && csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
    ...(init.headers as Record<string, string> | undefined),
  }
  const response = await fetch(authUrl(path), {
    ...init,
    method,
    headers,
    credentials: 'include',
  })
  if (!response.ok) {
    let message = response.status + ' ' + response.statusText
    try {
      const body = await response.json() as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
    } catch { /* response has no JSON body */ }
    const error = new Error(message) as Error & { status: number }
    error.status = response.status
    throw error
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function getAuthStatus() {
  return authRequest<{ setup_required: boolean }>('/auth/status')
}

export async function setupAdmin(payload: { email: string; password: string; display_name: string }) {
  const result = await authRequest<AuthResponse>('/auth/setup', { method: 'POST', body: JSON.stringify(payload) })
  csrfToken = result.csrf_token
  return result
}

export async function signIn(payload: { email: string; password: string }) {
  const result = await authRequest<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify(payload) })
  csrfToken = result.csrf_token
  return result
}

export async function getCurrentUser() {
  const result = await authRequest<AuthResponse>('/auth/me')
  csrfToken = result.csrf_token
  return result
}

export async function signOut() {
  try {
    await authRequest<{ signed_out: boolean }>('/auth/logout', { method: 'POST' })
  } catch {
    // A local sign-out still clears the browser state if the session already expired.
  } finally {
    csrfToken = ''
  }
}

export async function getAccounts() {
  return authRequest<SentinelUser[]>('/auth/users')
}

export async function createAccount(payload: AccountCreate) {
  return authRequest<SentinelUser>('/auth/users', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateAccount(id: string, payload: AccountPatch) {
  return authRequest<SentinelUser>('/auth/users/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(payload) })
}

export async function changePassword(current_password: string, new_password: string) {
  return authRequest<{ password_changed: boolean }>('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password, new_password }),
  })
}

export async function resetAccountPassword(id: string, new_password: string) {
  return authRequest<void>('/auth/users/' + encodeURIComponent(id) + '/password', {
    method: 'POST',
    body: JSON.stringify({ new_password }),
  })
}
