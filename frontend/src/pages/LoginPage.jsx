import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'
import { BookOpen, Eye, EyeOff, Mail } from 'lucide-react'

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [unverifiedEmail, setUnverifiedEmail] = useState(null)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendDone, setResendDone] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setUnverifiedEmail(null)
    try {
      // Step 1: get tokens
      const loginRes = await authApi.login(form)
      const { access_token, refresh_token } = loginRes.data

      // Step 2: fetch user profile — pass the token DIRECTLY, don't rely on the
      // Zustand store being updated yet (that's what caused the 401)
      const meRes = await authApi.me(access_token)

      // Step 3: only now save everything to the store and redirect
      setAuth(meRes.data, access_token, refresh_token)
      toast.success('Welcome back')
      navigate('/dashboard')
    } catch (err) {
      const httpStatus = err.response?.status
      const detail = err.response?.data?.detail || 'Login failed'

      if (httpStatus === 403) {
        setUnverifiedEmail(form.email)
      } else {
        toast.error(detail)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    setResendLoading(true)
    try {
      await authApi.resendVerification(unverifiedEmail)
      setResendDone(true)
      toast.success('Verification email sent — check your inbox')
    } catch {
      toast.error('Failed to resend. Please try again.')
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-parchment flex items-center justify-center px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-1 bg-ink" />
        <div className="absolute top-1 left-0 right-0 h-px bg-gold/40" />
      </div>

      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-ink mb-4">
            <BookOpen size={22} className="text-gold" />
          </div>
          <h1 className="font-display text-3xl text-ink mb-1">CIE Evaluator</h1>
          <p className="text-sm text-ink/40">Cambridge exam practice with AI feedback</p>
        </div>

        {/* Unverified email banner */}
        {unverifiedEmail && (
          <div className="border border-gold/40 bg-gold/10 p-4 mb-4 animate-fade-in">
            <div className="flex items-start gap-3">
              <Mail size={16} className="text-gold flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-ink font-medium mb-1">Email not verified</p>
                <p className="text-xs text-ink/60 mb-3">
                  Check your inbox for <strong>{unverifiedEmail}</strong> and click the
                  verification link. Can't find it?
                </p>
                {resendDone ? (
                  <p className="text-xs text-sage font-medium">
                    ✓ New link sent — check your inbox (and spam folder)
                  </p>
                ) : (
                  <button
                    onClick={handleResend}
                    disabled={resendLoading}
                    className="text-xs underline underline-offset-2 text-ink hover:text-crimson transition-colors disabled:opacity-50"
                  >
                    {resendLoading ? 'Sending…' : 'Resend verification email →'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Login card */}
        <div className="card p-8">
          <h2 className="font-display text-xl text-ink mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email address</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="input-field"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  required
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="input-field pr-10"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/30 hover:text-ink/60"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="divider my-6" />

          <p className="text-sm text-center text-ink/50">
            Don't have an account?{' '}
            <Link to="/register" className="text-ink hover:text-crimson underline underline-offset-2">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
