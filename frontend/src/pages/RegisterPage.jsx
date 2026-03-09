import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import toast from 'react-hot-toast'
import { BookOpen, Eye, EyeOff, CheckCircle } from 'lucide-react'

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', password: '', confirm_password: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm_password) {
      toast.error('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await authApi.register(form)
      setDone(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-screen bg-parchment flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center animate-fade-in">
          <div className="card p-10">
            <CheckCircle size={40} className="text-sage mx-auto mb-4" />
            <h2 className="font-display text-2xl text-ink mb-3">Check your email</h2>
            <p className="text-sm text-ink/60 leading-relaxed mb-6">
              We've sent a verification link to <strong>{form.email}</strong>.
              Click the link to activate your account.
            </p>
            <button onClick={() => navigate('/login')} className="btn-primary w-full">
              Return to login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-parchment flex items-center justify-center px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-1 bg-ink" />
        <div className="absolute top-1 left-0 right-0 h-px bg-gold/40" />
      </div>

      <div className="w-full max-w-sm animate-fade-in">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-ink mb-4">
            <BookOpen size={22} className="text-gold" />
          </div>
          <h1 className="font-display text-3xl text-ink mb-1">Papers CIE</h1>
          <p className="text-sm text-ink/40">Create your account</p>
        </div>

        <div className="card p-8">
          <h2 className="font-display text-xl text-ink mb-6">Register</h2>

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
              />
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  required
                  minLength={8}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="input-field pr-10"
                  placeholder="At least 8 characters"
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

            <div>
              <label className="label">Confirm password</label>
              <input
                type={showPass ? 'text' : 'password'}
                required
                value={form.confirm_password}
                onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                className="input-field"
                placeholder="Repeat password"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <div className="divider my-6" />

          <p className="text-sm text-center text-ink/50">
            Already have an account?{' '}
            <Link to="/login" className="text-ink hover:text-crimson underline underline-offset-2">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
