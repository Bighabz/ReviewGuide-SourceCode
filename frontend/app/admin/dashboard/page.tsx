'use client';

import AdminProtectedRoute from '@/components/AdminProtectedRoute';
import Dashboard from '../Dashboard';

export default function DashboardPage() {
  return (
    <AdminProtectedRoute>
      <Dashboard />
    </AdminProtectedRoute>
  );
}
