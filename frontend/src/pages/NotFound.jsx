/**
 * 404 Not Found page — catches unmatched routes.
 */

import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex-1 flex items-center justify-center px-6 py-16">
      <div className="text-center animate-fade-in">
        <p className="text-7xl font-black bg-gradient-to-br from-accent-cyan to-accent-violet bg-clip-text text-transparent mb-4">
          404
        </p>
        <h1 className="text-xl font-bold text-slate-100 mb-2">Page not found</h1>
        <p className="text-sm text-slate-400 mb-8 max-w-sm mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link to="/" className="btn-ghost px-5 py-2.5 text-sm no-underline">
            ← Home
          </Link>
          <Link to="/dashboard" className="btn-gradient px-5 py-2.5 text-sm no-underline">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
