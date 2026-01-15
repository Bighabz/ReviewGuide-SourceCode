'use client';

import AdminProtectedRoute from '@/components/AdminProtectedRoute';
import ConfigManagement from '../ConfigManagement';

export default function ConfigurationPage() {
  return (
    <AdminProtectedRoute>
      <ConfigManagement />
    </AdminProtectedRoute>
  );
}
