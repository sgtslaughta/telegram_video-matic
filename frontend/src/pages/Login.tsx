import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useLogin } from '@/hooks/useAuth'

export default function Login() {
  const navigate = useNavigate()
  const login = useLogin()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      await login.mutateAsync(password)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.')
    }
  }

  return (
    <motion.div
      className="flex min-h-screen items-center justify-center bg-white px-4 dark:bg-slate-950"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="w-full max-w-sm">
        <motion.div
          className="rounded-lg border border-gray-200 bg-white p-8 shadow-lg dark:border-slate-700 dark:bg-slate-900"
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="mb-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
            Login
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
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
                disabled={login.isPending}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none placeholder-gray-400 focus:border-[#229ED9] focus:ring-2 focus:ring-[#229ED9]/20 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder-gray-500 dark:focus:border-[#229ED9]"
                placeholder="Enter your password"
                autoFocus
              />
            </div>

            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={login.isPending || !password}
              className="w-full rounded-md bg-[#229ED9] px-4 py-2 font-medium text-white shadow-md transition-all hover:bg-[#1a7aaf] hover:shadow-lg hover:scale-[1.02] disabled:opacity-50 dark:hover:bg-[#1a7aaf]"
            >
              {login.isPending ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </motion.div>
      </div>
    </motion.div>
  )
}
