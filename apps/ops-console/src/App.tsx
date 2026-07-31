import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';

const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const RoutesPage = lazy(() => import('./pages/RoutesPage').then((module) => ({ default: module.RoutesPage })));
const ShipmentsPage = lazy(() => import('./pages/ShipmentsPage').then((module) => ({ default: module.ShipmentsPage })));
const AlertsPage = lazy(() => import('./pages/AlertsPage').then((module) => ({ default: module.AlertsPage })));
const AccountPage = lazy(() => import('./pages/AccountPage').then((module) => ({ default: module.AccountPage })));
const PlanningPage = lazy(() => import('./pages/PlanningPage').then((module) => ({ default: module.PlanningPage })));
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage').then((module) => ({ default: module.UnauthorizedPage })));
const UploadPage = lazy(() => import('./pages/UploadPage').then((module) => ({ default: module.UploadPage })));
const ProvidersPage = lazy(() => import('./pages/ProvidersPage').then((module) => ({ default: module.ProvidersPage })));

function RouteFallback() {
  return (
    <div className="rounded-[28px] border border-slate-800/80 bg-slate-950/72 px-5 py-5 text-sm text-slate-400 shadow-[0_24px_80px_rgba(2,12,20,0.34)]">
      Loading workspace surface...
    </div>
  );
}

export default function App() {
  return (
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
  );
}
