import { Fragment, useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { useTgStatus, useTgSetCredentials, useTgLoginPhone, useTgLoginCode, useTgLoginPassword, useTgLogout } from '@/hooks/useTgStatus'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AccountStatus } from '@/lib/types'

type Step = 'credentials' | 'phone' | 'code' | 'password' | 'confirmation'

export default function TelegramLoginFlow({ onConnected }: { onConnected?: () => void }): JSX.Element {
  const tgStatus = useTgStatus()
  const setCreds = useTgSetCredentials()
  const loginPhone = useTgLoginPhone()
  const loginCode = useTgLoginCode()
  const loginPassword = useTgLoginPassword()
  const logout = useTgLogout()

  const [apiId, setApiId] = useState('')
  const [apiHash, setApiHash] = useState('')
  const [editCreds, setEditCreds] = useState(false)
  const [stepOverride, setStepOverride] = useState<Step | null>(null)
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')

  // Determine current step based on status
  const getStep = (): Step => {
    if (!tgStatus.data) return 'phone'
    // No API credentials yet (or user chose to change them) → credentials step
    if (!tgStatus.data.configured || editCreds) return 'credentials'
    switch (tgStatus.data.status) {
      case AccountStatus.DISCONNECTED:
        return 'phone'
      case AccountStatus.WAITING_PHONE:
        return 'phone'
      case AccountStatus.WAITING_CODE:
        return 'code'
      case AccountStatus.WAITING_PASSWORD:
        return 'password'
      case AccountStatus.CONNECTED:
        return 'confirmation'
      default:
        return 'phone'
    }
  }

  // Step ordering for clamping manual (backward) navigation.
  const STEP_ORDER: Record<Step, number> = {
    credentials: 0, phone: 1, code: 2, password: 3, confirmation: 4,
  }
  const STEPPER: { step: Step; label: string; n: number }[] = [
    { step: 'phone', label: 'Phone', n: 1 },
    { step: 'code', label: 'Code', n: 2 },
    { step: 'password', label: 'Auth', n: 3 },
  ]
  const derivedStep = getStep()
  // Allow jumping back to an earlier step (corrections); never skip ahead.
  const currentStep =
    stepOverride && STEP_ORDER[stepOverride] <= STEP_ORDER[derivedStep]
      ? stepOverride
      : derivedStep

  // A stepper number is reachable only if it's at or before the real progress.
  const goToStep = (target: Step) => {
    if (STEP_ORDER[target] <= STEP_ORDER[derivedStep]) setStepOverride(target)
  }

  // Clear manual override whenever the backend status advances.
  useEffect(() => {
    setStepOverride(null)
  }, [tgStatus.data?.status])

  // Call onConnected when status becomes CONNECTED
  useEffect(() => {
    if (tgStatus.data?.status === AccountStatus.CONNECTED) {
      onConnected?.()
    }
  }, [tgStatus.data?.status, onConnected])

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiId.trim() || !apiHash.trim()) return
    try {
      await setCreds.mutateAsync({ apiId: apiId.trim(), apiHash: apiHash.trim() })
      setEditCreds(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Telegram request failed')
    }
  }

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!phone.trim()) return
    try {
      await loginPhone.mutateAsync(phone)
      setStepOverride(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Telegram request failed')
    }
  }

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim()) return
    try {
      await loginCode.mutateAsync(code)
      setStepOverride(null)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Telegram request failed')
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password.trim()) return
    try {
      await loginPassword.mutateAsync(password)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Telegram request failed')
    }
  }

  const handleLogout = async () => {
    try {
      await logout.mutateAsync()
      setPhone('')
      setCode('')
      setPassword('')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Telegram request failed')
    }
  }

  const stepVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3 },
    },
    exit: {
      opacity: 0,
      y: -20,
      transition: { duration: 0.2 },
    },
  }

  return (
    <div className="w-full">
      {/* Stepper Header (hidden on the pre-req credentials step) */}
      {currentStep !== 'credentials' && (
      <div className="mb-8 flex items-center justify-between">
        {STEPPER.map((s, i) => {
          const reached = STEP_ORDER[derivedStep] >= STEP_ORDER[s.step]
          const active = STEP_ORDER[currentStep] >= STEP_ORDER[s.step]
          return (
            <Fragment key={s.step}>
              {i > 0 && (
                <div className={`mx-2 h-0.5 flex-1 ${active ? 'bg-primary' : 'bg-muted'}`} />
              )}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => goToStep(s.step)}
                  disabled={!reached}
                  aria-label={`Go to ${s.label} step`}
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-colors ${
                    active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                  } ${reached ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}`}
                >
                  {s.n}
                </button>
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  {s.label}
                </div>
              </div>
            </Fragment>
          )
        })}
      </div>
      )}

      {/* Step Content */}
      <Card>
        <CardContent className="pt-8">
          <AnimatePresence mode="wait">
            {/* Credentials Step */}
            {currentStep === 'credentials' && (
              <motion.form
                key="credentials"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onSubmit={handleCredentialsSubmit}
                className="space-y-4"
              >
                <div>
                  <h2 className="mb-2 text-xl font-bold">Telegram API credentials</h2>
                  <p className="mb-4 text-xs text-muted-foreground">
                    Get these from{' '}
                    <a
                      href="https://my.telegram.org/apps"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary underline underline-offset-2"
                    >
                      my.telegram.org/apps
                    </a>
                    : log in with your phone → <span className="font-medium">API development tools</span> →
                    create an app (any title) → copy your <span className="font-medium">api_id</span> and{' '}
                    <span className="font-medium">api_hash</span>.
                  </p>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor="api_id">api_id</Label>
                      <Input
                        id="api_id"
                        inputMode="numeric"
                        value={apiId}
                        onChange={(e) => setApiId(e.target.value.replace(/\D/g, ''))}
                        disabled={setCreds.isPending}
                        placeholder="1234567"
                        autoFocus
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="api_hash">api_hash</Label>
                      <Input
                        id="api_hash"
                        value={apiHash}
                        onChange={(e) => setApiHash(e.target.value)}
                        disabled={setCreds.isPending}
                        placeholder="0123456789abcdef0123456789abcdef"
                      />
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={setCreds.isPending || !apiId.trim() || !apiHash.trim()}
                  className="w-full"
                >
                  {setCreds.isPending ? 'Saving...' : 'Continue'}
                </Button>
              </motion.form>
            )}

            {/* Phone Step */}
            {currentStep === 'phone' && (
              <motion.form
                key="phone"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onSubmit={handlePhoneSubmit}
                className="space-y-4"
              >
                <div>
                  <h2 className="mb-4 text-xl font-bold">Enter phone number</h2>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      disabled={loginPhone.isPending}
                      placeholder="+1 234 567 8900"
                      autoFocus
                    />
                    <p className="text-xs text-muted-foreground">
                      Include country code (e.g., +1 for US)
                    </p>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loginPhone.isPending || !phone.trim()}
                  className="w-full"
                >
                  {loginPhone.isPending ? 'Sending...' : 'Next'}
                </Button>
                <button
                  type="button"
                  onClick={() => setEditCreds(true)}
                  className="w-full text-center text-xs text-muted-foreground underline-offset-2 hover:underline"
                >
                  Change API credentials
                </button>
              </motion.form>
            )}

            {/* Code Step */}
            {currentStep === 'code' && (
              <motion.form
                key="code"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onSubmit={handleCodeSubmit}
                className="space-y-4"
              >
                <div>
                  <h2 className="mb-4 text-xl font-bold">Enter SMS code</h2>
                  <div className="space-y-2">
                    <Label htmlFor="code">Code</Label>
                    <Input
                      id="code"
                      type="text"
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                      disabled={loginCode.isPending}
                      placeholder="123456"
                      maxLength={6}
                      className="tracking-widest"
                      autoFocus
                    />
                    <p className="text-xs text-muted-foreground">
                      Check your Telegram for the code
                    </p>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loginCode.isPending || code.length < 5}
                  className="w-full"
                >
                  {loginCode.isPending ? 'Verifying...' : 'Next'}
                </Button>
              </motion.form>
            )}

            {/* Password Step */}
            {currentStep === 'password' && (
              <motion.form
                key="password"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onSubmit={handlePasswordSubmit}
                className="space-y-4"
              >
                <div>
                  <h2 className="mb-4 text-xl font-bold">Two-factor password</h2>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loginPassword.isPending}
                      placeholder="Enter your 2FA password"
                      autoFocus
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loginPassword.isPending || !password.trim()}
                  className="w-full"
                >
                  {loginPassword.isPending ? 'Verifying...' : 'Connect'}
                </Button>
              </motion.form>
            )}

            {/* Confirmation Step */}
            {currentStep === 'confirmation' && tgStatus.data && (
              <motion.div
                key="confirmation"
                variants={stepVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="space-y-4 text-center"
              >
                <div className="mb-6">
                  <h2 className="text-xl font-bold">Connected!</h2>
                  <p className="mt-4 text-4xl font-bold text-foreground">
                    {tgStatus.data.username
                      ? `@${tgStatus.data.username}`
                      : tgStatus.data.display_name || 'User'}
                  </p>
                  {tgStatus.data.phone && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      {tgStatus.data.phone}
                    </p>
                  )}
                </div>

                <Badge className="inline-block bg-secondary text-secondary-foreground hover:bg-secondary">
                  ✓ Account verified
                </Badge>

                <Button
                  onClick={handleLogout}
                  disabled={logout.isPending}
                  variant="outline"
                  className="w-full mt-6"
                >
                  {logout.isPending ? 'Logging out...' : 'Logout'}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </div>
  )
}
