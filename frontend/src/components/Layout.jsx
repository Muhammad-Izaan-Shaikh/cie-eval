import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../services/api'
import toast from 'react-hot-toast'
import { BookOpen, LayoutDashboard, Upload, LogOut } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch {}
    logout()
    navigate('/login')
    toast.success('Logged out')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="bg-ink text-parchment border-b border-ink-light">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen size={18} className="text-gold" />
            <span className="font-display text-base tracking-wide">PaperBot</span>
          </div>

          <nav className="flex items-center gap-6">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `flex items-center gap-1.5 text-xs tracking-widest uppercase transition-colors ${
                  isActive ? 'text-gold' : 'text-parchment/60 hover:text-parchment'
                }`
              }
            >
              <LayoutDashboard size={14} />
              Dashboard
            </NavLink>
            <NavLink
              to="/upload"
              className={({ isActive }) =>
                `flex items-center gap-1.5 text-xs tracking-widest uppercase transition-colors ${
                  isActive ? 'text-gold' : 'text-parchment/60 hover:text-parchment'
                }`
              }
            >
              <Upload size={14} />
              Upload Paper
            </NavLink>
          </nav>

          <div className="flex items-center gap-4">
            <span className="text-xs text-parchment/50">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-xs text-parchment/50 hover:text-parchment transition-colors"
            >
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-ink/10 py-4">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs text-ink/30">
          PaperBot — AI-assisted Cambridge exam practice
        </div>
      </footer>
    </div>
  )
}
