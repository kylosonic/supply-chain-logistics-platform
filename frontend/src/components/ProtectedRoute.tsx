import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types/auth';

export function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <p className="text-sm text-slate-600">Authenticating...</p>;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}
