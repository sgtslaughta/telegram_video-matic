import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogin } from '@/hooks/useAuth'
import Logo from '@/components/Logo'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function Login() {
  const navigate = useNavigate()
  const login = useLogin()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      // Trim so a pasted trailing newline/space doesn't cause a false reject.
      await login.mutateAsync(password.trim())
      navigate('/')
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : 'Login failed. Check the password and try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <Logo className="h-16 w-16" title="TGVM" />
          <h1 className="text-[20px] font-semibold tracking-tight">Login</h1>
          <p className="text-[13px] text-muted-foreground">Enter the password to open your library.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-border bg-card p-5">
          <div className="space-y-1.5">
            <Label htmlFor="password" className="text-[13px]">Password</Label>
            <Input id="password" type="password" autoComplete="current-password" value={password}
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              disabled={login.isPending} placeholder="Enter your password" autoFocus
              aria-invalid={!!error} aria-describedby={error ? 'login-error' : undefined} />
            {error && <p id="login-error" role="alert" className="text-[12px] text-err">{error}</p>}
          </div>
          <Button type="submit" disabled={login.isPending || !password} className="w-full">
            {login.isPending ? 'Logging in…' : 'Login'}
          </Button>
        </form>
      </div>
    </div>
  )
}
