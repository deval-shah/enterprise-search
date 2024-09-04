// useSessionRefresh.ts
import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

export const useSessionRefresh = () => {
  const { refreshSession, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const refreshInterval = setInterval(async () => {
      const refreshed = await refreshSession();
      if (!refreshed) {
        await logout();
        router.push('/login');
      }
    }, 15 * 60 * 1000); // Refresh every 15 minutes

    return () => clearInterval(refreshInterval);
  }, [refreshSession, logout, router]);

  // Add a listener for WebSocket disconnection
  useEffect(() => {
    const handleWebSocketDisconnect = () => {
      logout();
      router.push('/login');
    };

    window.addEventListener('websocket_disconnect', handleWebSocketDisconnect);

    return () => {
      window.removeEventListener('websocket_disconnect', handleWebSocketDisconnect);
    };
  }, [logout, router]);
};
