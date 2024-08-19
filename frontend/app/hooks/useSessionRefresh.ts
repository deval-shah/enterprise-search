// useSessionRefresh.ts
import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/router';

export const useSessionRefresh = () => {
  const { refreshSession, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const refreshInterval = setInterval(async () => {
      const refreshed = await refreshSession();
      if (!refreshed) {
        // Handle failed refresh by logging out and redirecting to login
        await logout();
        router.push('/login');
      }
    }, 15 * 60 * 1000); // Refresh every 15 minutes

    return () => clearInterval(refreshInterval);
  }, [refreshSession, logout, router]);
};