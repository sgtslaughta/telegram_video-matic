import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTgStatus, useTgLoginPhone, useTgLoginCode, useTgLoginPassword, useTgLogout } from '@/hooks/useTgStatus'
import { AccountStatus } from '@/lib/types'

type Step = 'phone' | 'code' | 'password' | 'confirmation'

export default function Connect() {
  const tgStatus = useTgStatus()
  const loginPhone = useTgLoginPhone()
  const loginCode = useTgLoginCode()
  const loginPassword = useTgLoginPassword()
  const logout = useTgLogout()

  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')

  // Determine current step based on status
  const getStep = (): Step => {
    if (!tgStatus.data) return 'phone'
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

  const currentStep = getStep()

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!phone.trim()) return
    try {
      await loginPhone.mutateAsync(phone)
    } catch (err) {
      console.error(err)
    }
  }

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim()) return
    try {
      await loginCode.mutateAsync(code)
    } catch (err) {
      console.error(err)
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password.trim()) return
    try {
      await loginPassword.mutateAsync(password)
    } catch (err) {
      console.error(err)
    }
  }

  const handleLogout = async () => {
    try {
      await logout.mutateAsync()
      setPhone('')
      setCode('')
      setPassword('')
    } catch (err) {
      console.error(err)
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
    <div className="flex min-h-screen items-center justify-center bg-white px-4 dark:bg-slate-950">
      <div className="w-full max-w-md">
        {/* Stepper Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                ['phone', 'code'].includes(currentStep)
                  ? 'bg-[#229ED9] text-white'
                  : 'bg-gray-200 text-gray-600 dark:bg-slate-700 dark:text-gray-400'
              }`}
            >
              1
            </div>
            <div className="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">
              Phone
            </div>
          </div>

          <div
            className={`h-0.5 flex-1 mx-2 ${
              ['code', 'password', 'confirmation'].includes(currentStep)
                ? 'bg-[#229ED9]'
                : 'bg-gray-200 dark:bg-slate-700'
            }`}
          />

          <div className="flex items-center gap-4">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                ['code', 'password', 'confirmation'].includes(currentStep)
                  ? 'bg-[#229ED9] text-white'
                  : 'bg-gray-200 text-gray-600 dark:bg-slate-700 dark:text-gray-400'
              }`}
            >
              2
            </div>
            <div className="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">
              Code
            </div>
          </div>

          <div
            className={`h-0.5 flex-1 mx-2 ${
              ['password', 'confirmation'].includes(currentStep)
                ? 'bg-[#229ED9]'
                : 'bg-gray-200 dark:bg-slate-700'
            }`}
          />

          <div className="flex items-center gap-4">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${
                ['password', 'confirmation'].includes(currentStep)
                  ? 'bg-[#229ED9] text-white'
                  : 'bg-gray-200 text-gray-600 dark:bg-slate-700 dark:text-gray-400'
              }`}
            >
              3
            </div>
            <div className="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">
              Auth
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="rounded-lg border border-gray-200 bg-white p-8 dark:border-slate-700 dark:bg-slate-900">
          <AnimatePresence mode="wait">
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
                  <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">
                    Enter phone number
                  </h2>
                  <label
                    htmlFor="phone"
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Phone
                  </label>
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    disabled={loginPhone.isPending}
                    placeholder="+1 234 567 8900"
                    className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none placeholder-gray-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-gray-500"
                    autoFocus
                  />
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Include country code (e.g., +1 for US)
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loginPhone.isPending || !phone.trim()}
                  className="w-full rounded-md bg-[#229ED9] px-4 py-2 font-medium text-white hover:bg-[#1a7aaf] disabled:opacity-50 dark:hover:bg-[#1a7aaf]"
                >
                  {loginPhone.isPending ? 'Sending...' : 'Next'}
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
                  <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">
                    Enter SMS code
                  </h2>
                  <label
                    htmlFor="code"
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Code
                  </label>
                  <input
                    id="code"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                    disabled={loginCode.isPending}
                    placeholder="123456"
                    maxLength={6}
                    className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm tracking-widest outline-none placeholder-gray-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-gray-500"
                    autoFocus
                  />
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Check your Telegram for the code
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loginCode.isPending || code.length < 5}
                  className="w-full rounded-md bg-[#229ED9] px-4 py-2 font-medium text-white hover:bg-[#1a7aaf] disabled:opacity-50 dark:hover:bg-[#1a7aaf]"
                >
                  {loginCode.isPending ? 'Verifying...' : 'Next'}
                </button>
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
                  <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">
                    Two-factor password
                  </h2>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loginPassword.isPending}
                    placeholder="Enter your 2FA password"
                    className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none placeholder-gray-400 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-gray-500"
                    autoFocus
                  />
                </div>

                <button
                  type="submit"
                  disabled={loginPassword.isPending || !password.trim()}
                  className="w-full rounded-md bg-[#229ED9] px-4 py-2 font-medium text-white hover:bg-[#1a7aaf] disabled:opacity-50 dark:hover:bg-[#1a7aaf]"
                >
                  {loginPassword.isPending ? 'Verifying...' : 'Connect'}
                </button>
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
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Connected!
                  </h2>
                  <p className="mt-4 text-4xl font-bold text-[#229ED9]">
                    {tgStatus.data.username
                      ? `@${tgStatus.data.username}`
                      : tgStatus.data.display_name || 'User'}
                  </p>
                  {tgStatus.data.phone && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {tgStatus.data.phone}
                    </p>
                  )}
                </div>

                <div className="inline-block rounded-full bg-green-100 px-4 py-2 text-sm font-medium text-green-800 dark:bg-green-900/20 dark:text-green-300">
                  ✓ Account verified
                </div>

                <button
                  onClick={handleLogout}
                  disabled={logout.isPending}
                  className="mt-6 w-full rounded-md border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-slate-600 dark:text-gray-300 dark:hover:bg-slate-800"
                >
                  {logout.isPending ? 'Logging out...' : 'Logout'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
