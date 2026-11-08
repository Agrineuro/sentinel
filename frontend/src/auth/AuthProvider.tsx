import { createContext, useCallback, useContext, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { KeyRound, ShieldCheck } from 'lucide-react'
import { getAuthStatus, getCurrentUser, signIn, signOut, setupAdmin, type SentinelUser } from '../api/auth'

interface AuthContextValue {
  user: SentinelUser
  logout: () => Promise<void>
}
const AuthContext = createContext<AuthContextValue | null>(null)

type ScreenMode = 'checking' | 'setup' | 'login' | 'error' | 'ready'

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ScreenMode>('checking')
  const [user, setUser] = useState<SentinelUser | null>(null)
  const [error, setError] = useState('')
  const [working, setWorking] = useState(false)

  const initialize = useCallback(async () => {
    setMode('checking')
    setError('')
    try {
      const status = await getAuthStatus()
      if (status.setup_required) {
        setMode('setup')
        return
      }
      try {
        const current = await getCurrentUser()
        setUser(current)
        setMode('ready')
      } catch (authError) {
        if (authError instanceof Error && (authError as Error & { status?: number }).status === 401) {
          setMode('login')
        } else {
          throw authError
        }
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Could not connect to Sentinel')
      setMode('error')
    }
  }, [])

  useEffect(() => { void initialize() }, [initialize])
  useEffect(() => {
    const expired = () => {
      setUser(null)
      setMode('login')
      setError('Your session expired. Sign in again.')
    }
    window.addEventListener('sentinel:auth-expired', expired)
    return () => window.removeEventListener('sentinel:auth-expired', expired)
  }, [])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setWorking(true)
    setError('')
    const form = new FormData(event.currentTarget)
    try {
      const auth = mode === 'setup'
        ? await setupAdmin({
            display_name: String(form.get('display_name') ?? '').trim(),
            email: String(form.get('email') ?? '').trim(),
            password: String(form.get('password') ?? ''),
          })
        : await signIn({
            email: String(form.get('email') ?? '').trim(),
            password: String(form.get('password') ?? ''),
          })
      setUser(auth)
      setMode('ready')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Sign-in failed')
    } finally {
      setWorking(false)
    }
  }

  const logout = async () => {
    await signOut()
    setUser(null)
    setMode('login')
    setError('')
  }

  if (mode === 'checking') return <div className="auth-loading">Connecting to Sentinel…</div>
  if (mode !== 'ready') {
    const settingUp = mode === 'setup'
    return (
      <main className="auth-screen">
        <section className="auth-card panel">
          <div className="auth-brand"><span><ShieldCheck size={25} /></span><div><strong>SENTINEL</strong><small>Infrastructure operating environment</small></div></div>
          <div className="auth-heading">
            <span className="detail-kicker">{mode === 'error' ? 'Connection required' : settingUp ? 'First-time setup' : 'Secure sign-in'}</span>
            <h1>{mode === 'error' ? 'Sentinel Core is unavailable' : settingUp ? 'Create the administrator account' : 'Sign in to Sentinel'}</h1>
            <p>{mode === 'error' ? 'Check that Core is running and the dashboard URL is correct.' : settingUp ? 'This account will manage users and configure Sentinel.' : 'Use the account created during first-time setup.'}</p>
          </div>
          {mode === 'error' ? (
            <div className="auth-error" role="alert">{error}<button className="primary-button" onClick={() => void initialize()}>Retry connection</button></div>
          ) : (
            <form className="auth-form" onSubmit={submit}>
              {settingUp && <label>Display name<input name="display_name" required maxLength={120} autoComplete="name" /></label>}
              <label>Email<input name="email" type="email" required maxLength={320} autoComplete="username" /></label>
              <label>Password<input name="password" type="password" required minLength={12} maxLength={72} autoComplete={settingUp ? 'new-password' : 'current-password'} /></label>
              {settingUp && <small className="auth-hint">Use at least 12 characters. This is the only public account creation step.</small>}
              {error && <p className="auth-error" role="alert">{error}</p>}
              <button className="primary-button" disabled={working}>{working ? 'Please wait…' : settingUp ? <><KeyRound size={16} /> Create admin account</> : 'Sign in'}</button>
            </form>
          )}
          <div className="auth-footnote">Account sessions expire after 12 hours. Keep Sentinel behind HTTPS when accessed over a network.</div>
        </section>
      </main>
    )
  }

  return <AuthContext.Provider value={{ user: user!, logout }}>{children}</AuthContext.Provider>
}
