/**
 * App layout + React Router configuration.
 *
 * Hardened with:
 * - Global ErrorBoundary (catches render crashes)
 * - HealthBanner (polls backend health, shows status)
 * - 404 catch-all route
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import HealthBanner from './components/HealthBanner';
import ToastContainer from './components/Toast';
import Navbar from './components/Navbar';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import AnalysisDetail from './pages/AnalysisDetail';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <ErrorBoundary>
      <ToastContainer />
      <BrowserRouter>
        <AuthProvider>
          {/* Health status banner — sticky top */}
          <HealthBanner />

          {/* Mesh background */}
          <div className="mesh-bg fixed inset-0 -z-10 overflow-hidden pointer-events-none" />

          {/* App shell */}
          <div className="min-h-screen flex flex-col">
            <Navbar />
            <Routes>
              {/* Public */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/history"
                element={
                  <ProtectedRoute>
                    <History />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analysis/:id"
                element={
                  <ProtectedRoute>
                    <AnalysisDetail />
                  </ProtectedRoute>
                }
              />

              {/* 404 catch-all */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
