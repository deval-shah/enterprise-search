// hooks/useFirebaseAuth.ts
import { useState, useEffect, useCallback } from 'react';
import { User, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { auth } from '../lib/firebase';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export function useFirebaseAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });
  const [sessionToken, setSessionToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('sessionToken');
    }
    return null;
  });

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      setAuthState({ user, loading: false, error: null });
    });

    return () => unsubscribe();
  }, []);

  
  const clearAuthState = useCallback(() => {
    setAuthState({ user: null, loading: false, error: null });
    setSessionToken(null);
    // Clear any stored tokens or cookies
    localStorage.removeItem('sessionToken');
    document.cookie = 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const token = await userCredential.user.getIdToken();
      return token;
    } catch (error) {
      if (error instanceof Error) {
        setAuthState(prev => ({ ...prev, error: error.message }));
      } else {
        setAuthState(prev => ({ ...prev, error: 'An unknown error occurred' }));
      }
      throw error;
    }
  }, []);

  const getAuthHeaders = useCallback((): HeadersInit => {
    const token = sessionToken || (typeof window !== 'undefined' ? localStorage.getItem('sessionToken') : null);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }, [sessionToken]);
  
  const makeAuthenticatedRequest = useCallback(async (url: string, options: RequestInit = {}) => {
    const headers = getAuthHeaders();
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        ...headers,
      },
      credentials: 'include',
    });

    if (response.status === 401) {
      clearAuthState();
      throw new Error('Unauthorized');
    }

    return response;
  }, [getAuthHeaders, clearAuthState]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const firebaseToken = await userCredential.user.getIdToken();
      
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Failed to get session token');
      }

      const { sessionToken } = await response.json();
      setSessionToken(sessionToken);
      localStorage.setItem('sessionToken', sessionToken);
      document.cookie = `session_token=${sessionToken}; path=/; max-age=3600; SameSite=Strict; Secure`;
      return sessionToken;
    } catch (error) {
      if (error instanceof Error) {
        setAuthState(prev => ({ ...prev, error: error.message }));
      } else {
        setAuthState(prev => ({ ...prev, error: 'An unknown error occurred' }));
      }
      throw error;
    }
  }, []);
  
  const logout = useCallback(async () => {
    try {
      await signOut(auth);
      await makeAuthenticatedRequest('/api/logout', {
        method: 'POST',
      });
      clearAuthState();
    } catch (error) {
      if (error instanceof Error) {
        setAuthState(prev => ({ ...prev, error: error.message }));
      } else {
        setAuthState(prev => ({ ...prev, error: 'An unknown error occurred' }));
      }
      throw error;
    }
  }, [makeAuthenticatedRequest, clearAuthState]);

  return {
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    register,
    login,
    logout,
    getAuthHeaders,
    makeAuthenticatedRequest,
  };
}
