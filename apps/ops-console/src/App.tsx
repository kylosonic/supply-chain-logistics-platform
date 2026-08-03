import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { ErrorBoundary } from './components/ErrorBoundary';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';

const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const RoutesPage = lazy(() => import('./pages/RoutesPage').then((m) => ({ default: m.RoutesPage })));
const ShipmentsPage = lazy(() => import('./pages/ShipmentsPage').then((m) => ({ default: m.ShipmentsPage })));
const AlertsPage = lazy(() => import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage })));
const AccountPage = lazy(() => import('./pages/AccountPage').then((m) => ({ default: m.AccountPage })));
const PlanningPage = lazy(() => import('./pages/PlanningPage').then((m) => ({ default: m.PlanningPage })));
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage').then((m) => ({ default: m.UnauthorizedPage })));
const UploadPage = lazy(() => import('./pages/UploadPage').then((m) => ({ default: m.UploadPage })));
const ProvidersPage = lazy(() => import('./pages/ProvidersPage').then((m) => ({ default: m.ProvidersPage })));

function RouteFallback() {
  return (
    <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/72 px-5 py-5 text-sm text-slate-400 shadow-[0_24px_80px_rgba(2,12,20,0.34)]">
      Loading workspace surface...
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <DashboardPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/routes"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                <Layout>
                  <RoutesPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/upload"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator']}>
                <Layout>
                  <UploadPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/shipments"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                <Layout>
                  <ShipmentsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/alerts"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                <Layout>
                  <AlertsPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/planning"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                <Layout>
                  <PlanningPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/account"
            element={
              <ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}>
                <Layout>
                  <AccountPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/providers"
            element={
              <ProtectedRoute allowedRoles={['admin', 'owner', 'operator']}>
                <Layout>
                  <ProvidersPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
