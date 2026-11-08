import { useEffect, useState, type FormEvent } from 'react'
import { changePassword, createAccount, getAccounts, resetAccountPassword, updateAccount, type AccountRole, type SentinelUser } from '../api/auth'
import { useAuth } from '../auth/AuthProvider'

export function AccountManagementPanel() {
  const { user } = useAuth()
  const [accounts, setAccounts] = useState<SentinelUser[]>([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = async () => {
    try { setAccounts(await getAccounts()); setError('') }
    catch (loadError) { setError(loadError instanceof Error ? loadError.message : 'Could not load accounts') }
  }
  useEffect(() => { if (user.role === 'admin') void refresh() }, [user.role])

  const submitNewAccount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    setBusy(true); setError(''); setNotice('')
    try {
      await createAccount({
        display_name: String(values.get('display_name') ?? '').trim(),
        email: String(values.get('email') ?? '').trim(),
        password: String(values.get('password') ?? ''),
        role: String(values.get('role') ?? 'viewer') as AccountRole,
      })
      form.reset()
      setNotice('Account created.')
      await refresh()
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Could not create account')
    } finally { setBusy(false) }
  }

  const changeRole = async (account: SentinelUser, role: AccountRole) => {
    setError(''); setNotice('')
    try { await updateAccount(account.id, { role }); await refresh() }
    catch (updateError) { setError(updateError instanceof Error ? updateError.message : 'Could not update account') }
  }

  const resetPassword = async (account: SentinelUser) => {
    const password = window.prompt('Set a temporary password for ' + account.email + '. Use at least 12 characters.')
    if (!password) return
    setError(''); setNotice('')
    try {
      await resetAccountPassword(account.id, password)
      setNotice('Password reset. Share the temporary password securely; the user must sign in again.')
      await refresh()
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : 'Could not reset password')
    }
  }

  const toggleActive = async (account: SentinelUser) => {
    setError(''); setNotice('')
    try { await updateAccount(account.id, { is_active: !account.is_active }); await refresh() }
    catch (updateError) { setError(updateError instanceof Error ? updateError.message : 'Could not update account') }
  }

  const updateOwnPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    setBusy(true); setError(''); setNotice('')
    try {
      await changePassword(String(values.get('current_password') ?? ''), String(values.get('new_password') ?? ''))
      setNotice('Password changed. Sign in again with the new password.')
      form.reset()
      window.dispatchEvent(new Event('sentinel:auth-expired'))
    } catch (changeError) {
      setError(changeError instanceof Error ? changeError.message : 'Could not change password')
    } finally { setBusy(false) }
  }

  return (
    <section className="panel account-panel settings-card">
      <div className="settings-card-title">
        <div><h2>Accounts and access</h2><p>Manage who can view and change this Sentinel installation.</p></div>
      </div>
      {user.role === 'admin' ? <>
        <div className="account-list">
          {accounts.map(account => <div className="account-row" key={account.id}>
            <div><strong>{account.display_name}</strong><small>{account.email}{account.id === user.id ? ' · You' : ''}</small></div>
            <select aria-label={'Role for ' + account.email} value={account.role} disabled={account.id === user.id} onChange={event => void changeRole(account, event.target.value as AccountRole)}>
              <option value="admin">Admin</option><option value="operator">Operator</option><option value="viewer">Viewer</option>
            </select>
            <button className="secondary-button" disabled={account.id === user.id} onClick={() => void resetPassword(account)}>Reset password</button><button className="secondary-button" disabled={account.id === user.id} onClick={() => void toggleActive(account)}>{account.is_active ? 'Disable' : 'Enable'}</button>
            {!account.is_active && <span className="account-disabled">Disabled</span>}
          </div>)}
        </div>
        <form className="account-create-form" onSubmit={submitNewAccount}>
          <h3>Add an account</h3>
          <label>Name<input name="display_name" required maxLength={120} /></label>
          <label>Email<input name="email" type="email" required maxLength={320} /></label>
          <label>Temporary password<input name="password" type="password" required minLength={12} maxLength={72} autoComplete="new-password" /></label>
          <label>Role<select name="role" defaultValue="viewer"><option value="viewer">Viewer · read only</option><option value="operator">Operator · make changes</option><option value="admin">Admin · manage accounts</option></select></label>
          <button className="primary-button" disabled={busy}>Create account</button>
          <small>Share the temporary password securely. Users can change it after signing in.</small>
        </form>
      </> : <p className="account-readonly">Only administrators can manage accounts.</p>}
      <form className="password-change-form" onSubmit={updateOwnPassword}>
        <h3>Change your password</h3>
        <label>Current password<input name="current_password" type="password" required autoComplete="current-password" /></label>
        <label>New password<input name="new_password" type="password" required minLength={12} maxLength={72} autoComplete="new-password" /></label>
        <button className="secondary-button" disabled={busy}>Change password</button>
      </form>
      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="form-success" role="status">{notice}</p>}
    </section>
  )
}
