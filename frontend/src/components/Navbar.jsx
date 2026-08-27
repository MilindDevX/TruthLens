/**
 * Top navigation bar with mobile hamburger menu.
 */

import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setMobileOpen(false);
    navigate('/');
  };

  const closeMobile = () => setMobileOpen(false);

  const isActive = (path) =>
    location.pathname === path ? 'text-accent-cyan' : 'text-slate-300 hover:text-accent-cyan';

  return (
    <nav className="sticky top-0 z-50 bg-surface-primary/80 backdrop-blur-xl border-b border-border-glass">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group" onClick={closeMobile}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center text-white font-bold text-sm transition-shadow duration-300 group-hover:shadow-glow-cyan">
            TL
          </div>
          <span className="text-lg font-bold text-slate-100">
            Truth<span className="text-accent-cyan">Lens</span>
          </span>
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-6">
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard"
                className={`text-sm font-medium transition-colors ${isActive('/dashboard')}`}
              >
                Analyze
              </Link>
              <Link
                to="/history"
                className={`text-sm font-medium transition-colors ${isActive('/history')}`}
              >
                History
              </Link>
              <div className="h-5 w-px bg-border-glass" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 border border-border-glass flex items-center justify-center text-xs font-semibold text-accent-cyan">
                  {user?.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <button
                  onClick={handleLogout}
                  className="text-sm font-medium text-slate-400 hover:text-red-400 transition-colors"
                >
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className={`text-sm font-medium transition-colors ${isActive('/login')}`}
              >
                Login
              </Link>
              <Link to="/register" className="btn-gradient text-xs px-4 py-2">
                Get Started
              </Link>
            </>
          )}
        </div>

        {/* Mobile Hamburger */}
        <button
          onClick={() => setMobileOpen((prev) => !prev)}
          className="md:hidden flex flex-col items-center justify-center w-9 h-9 gap-1.5 rounded-lg bg-surface-glass border border-border-glass transition-colors hover:border-border-glass-hover"
          aria-label="Toggle menu"
          aria-expanded={mobileOpen}
        >
          <span
            className={`block w-4 h-0.5 bg-slate-300 rounded-full transition-all duration-300 ${
              mobileOpen ? 'rotate-45 translate-y-1' : ''
            }`}
          />
          <span
            className={`block w-4 h-0.5 bg-slate-300 rounded-full transition-all duration-300 ${
              mobileOpen ? 'opacity-0' : ''
            }`}
          />
          <span
            className={`block w-4 h-0.5 bg-slate-300 rounded-full transition-all duration-300 ${
              mobileOpen ? '-rotate-45 -translate-y-1' : ''
            }`}
          />
        </button>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border-glass bg-surface-primary/95 backdrop-blur-xl animate-slide-down">
          <div className="px-6 py-4 space-y-1">
            {isAuthenticated ? (
              <>
                {/* User info */}
                <div className="flex items-center gap-3 pb-3 mb-3 border-b border-border-glass">
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-violet/20 border border-border-glass flex items-center justify-center text-sm font-semibold text-accent-cyan">
                    {user?.email?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{user?.full_name || user?.email}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                </div>

                <Link
                  to="/dashboard"
                  onClick={closeMobile}
                  className="block py-2.5 px-3 text-sm font-medium text-slate-300 hover:text-accent-cyan hover:bg-surface-glass rounded-lg transition-all"
                >
                  🔍 Analyze
                </Link>
                <Link
                  to="/history"
                  onClick={closeMobile}
                  className="block py-2.5 px-3 text-sm font-medium text-slate-300 hover:text-accent-cyan hover:bg-surface-glass rounded-lg transition-all"
                >
                  📋 History
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left py-2.5 px-3 text-sm font-medium text-red-400 hover:bg-red-500/10 rounded-lg transition-all mt-2"
                >
                  ↩ Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={closeMobile}
                  className="block py-2.5 px-3 text-sm font-medium text-slate-300 hover:text-accent-cyan hover:bg-surface-glass rounded-lg transition-all"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  onClick={closeMobile}
                  className="block mt-2"
                >
                  <span className="btn-gradient w-full text-sm py-2.5">Get Started</span>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
