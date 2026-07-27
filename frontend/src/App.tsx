import { Navigate, Route, Routes } from 'react-router-dom';

import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RoutesPage } from './pages/RoutesPage';
import { ShipmentsPage } from './pages/ShipmentsPage';
import { AlertsPage } from './pages/AlertsPage';
import { PlanningPage } from './pages/PlanningPage';
import { UnauthorizedPage } from './pages/UnauthorizedPage';
import { UploadPage } from './pages/UploadPage';

export default function App() {
  return (
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

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
