/**
 * Top navigation bar with user menu.
 */

import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-50 bg-surface-primary/80 backdrop-blur-xl border-b border-border-glass">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-violet flex items-center justify-center text-white font-bold text-sm transition-shadow duration-300 group-hover:shadow-glow-cyan">
            TL
          </div>
          <span className="text-lg font-bold text-slate-100">
            Truth<span className="text-accent-cyan">Lens</span>
          </span>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-6">
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard"
                className="text-sm font-medium text-slate-300 hover:text-accent-cyan transition-colors"
              >
                Analyze
              </Link>
              <Link
                to="/history"
                className="text-sm font-medium text-slate-300 hover:text-accent-cyan transition-colors"
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
                className="text-sm font-medium text-slate-300 hover:text-accent-cyan transition-colors"
              >
                Login
              </Link>
              <Link to="/register" className="btn-gradient text-xs px-4 py-2">
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
