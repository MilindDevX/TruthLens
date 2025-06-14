/**
 * Global Error Boundary — catches unhandled React rendering errors
 * and shows a graceful fallback UI instead of a white screen.
 *
 * Must be a class component (React error boundaries don't support hooks yet).
 */

import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to console (replace with remote logging in production)
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center px-6 bg-surface-primary">
          <div className="max-w-md w-full text-center animate-fade-in">
            {/* Icon */}
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <svg className="w-10 h-10 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
            </div>

            {/* Message */}
            <h1 className="text-2xl font-bold text-slate-100 mb-2">Something went wrong</h1>
            <p className="text-slate-400 text-sm mb-6 leading-relaxed">
              An unexpected error occurred while rendering this page.
              Your data is safe — try refreshing or go back.
            </p>

            {/* Error details (dev only) */}
            {import.meta.env.DEV && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400 transition-colors">
                  Technical details
                </summary>
                <pre className="mt-2 p-3 bg-surface-glass border border-border-glass rounded-xl text-xs text-red-400 overflow-auto max-h-40">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            {/* Actions */}
            <div className="flex items-center justify-center gap-3">
              <button onClick={this.handleReset} className="btn-ghost px-5 py-2.5 text-sm">
                ← Try Again
              </button>
              <button onClick={this.handleReload} className="btn-gradient px-5 py-2.5 text-sm">
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
