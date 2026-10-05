import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { ErrorBoundary } from './components/ErrorBoundary';
import { Layout, RouteFallback } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';

const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const RoutesPage = lazy(() => import('./pages/RoutesPage').then((m) => ({ default: m.RoutesPage })));
const ShipmentsPage = lazy(() => import('./pages/ShipmentsPage').then((m) => ({ default: m.ShipmentsPage })));
const DriversPage = lazy(() => import('./pages/DriversPage').then((m) => ({ default: m.DriversPage })));
const AlertsPage = lazy(() => import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage })));
const AccountPage = lazy(() => import('./pages/AccountPage').then((m) => ({ default: m.AccountPage })));
const PlanningPage = lazy(() => import('./pages/PlanningPage').then((m) => ({ default: m.PlanningPage })));
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage').then((m) => ({ default: m.UnauthorizedPage })));
const UploadPage = lazy(() => import('./pages/UploadPage').then((m) => ({ default: m.UploadPage })));
const ProvidersPage = lazy(() => import('./pages/ProvidersPage').then((m) => ({ default: m.ProvidersPage })));
const ReceiptsPage = lazy(() => import('./pages/ReceiptsPage').then((m) => ({ default: m.ReceiptsPage })));
const AdminReceiptsPage = lazy(() => import('./pages/AdminReceiptsPage').then((m) => ({ default: m.AdminReceiptsPage })));

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* TECH-72: ONE layout route with an auth-only gate — unauthenticated
              users redirect to /login before the shell can mount (decision 1);
              every child keeps its own role-gated ProtectedRoute. */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/routes" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><RoutesPage /></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute allowedRoles={['admin', 'operator']}><UploadPage /></ProtectedRoute>} />
            <Route path="/shipments" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><ShipmentsPage /></ProtectedRoute>} />
            <Route path="/drivers" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><DriversPage /></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><AlertsPage /></ProtectedRoute>} />
            <Route path="/planning" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><PlanningPage /></ProtectedRoute>} />
            <Route path="/account" element={<ProtectedRoute allowedRoles={['admin', 'operator', 'viewer']}><AccountPage /></ProtectedRoute>} />
            <Route path="/providers" element={<ProtectedRoute allowedRoles={['admin', 'owner', 'operator']}><ProvidersPage /></ProtectedRoute>} />
            <Route path="/receipts" element={<ProtectedRoute allowedRoles={['admin', 'owner', 'operator', 'viewer']}><ReceiptsPage /></ProtectedRoute>} />
            <Route path="/admin/receipts" element={<ProtectedRoute allowedRoles={['admin', 'owner']}><AdminReceiptsPage /></ProtectedRoute>} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
