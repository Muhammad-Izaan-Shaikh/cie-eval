import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('loading')
  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      return
    }
    authApi.verifyEmail(token)
      .then(() => setStatus('success'))
      .catch(() => setStatus('error'))
  }, [token])

  return (
    <div className="min-h-screen bg-parchment flex items-center justify-center px-4">
      <div className="card p-10 w-full max-w-sm text-center animate-fade-in">
        {status === 'loading' && (
          <>
            <Loader size={36} className="text-gold mx-auto mb-4 animate-spin" />
            <h2 className="font-display text-xl text-ink">Verifying your email…</h2>
          </>
        )}
        {status === 'success' && (
          <>
            <CheckCircle size={40} className="text-sage mx-auto mb-4" />
            <h2 className="font-display text-2xl text-ink mb-3">Email verified</h2>
            <p className="text-sm text-ink/60 mb-6">Your account is now active. You can sign in.</p>
            <button onClick={() => navigate('/login')} className="btn-primary w-full">
              Sign in
            </button>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle size={40} className="text-crimson mx-auto mb-4" />
            <h2 className="font-display text-2xl text-ink mb-3">Verification failed</h2>
            <p className="text-sm text-ink/60 mb-6">
              The link is invalid or has expired. Please register again.
            </p>
            <button onClick={() => navigate('/register')} className="btn-secondary w-full">
              Back to register
            </button>
          </>
        )}
      </div>
    </div>
  )
}
