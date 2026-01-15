'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, CircularProgress } from '@mui/material';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export default function AdminPage() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAdminAuth();

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        router.push('/admin/dashboard');
      } else {
        router.push('/admin/login');
      }
    }
  }, [isAuthenticated, loading, router]);

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--gpt-background)',
      }}
    >
      <CircularProgress sx={{ color: 'var(--gpt-accent)' }} />
    </Box>
  );
}
