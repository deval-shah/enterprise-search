// app/contexts/AuthContext.tsx
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';
import { auth } from '../lib/firebase';
import WebSocketService from '../services/WebSocketService';
import { useAuthStore } from '../store';

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is not defined');
}

interface AuthContextType {
  login: (email: string, password: string) => Promise<Boolean>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  webSocketService: WebSocketService | null;
  refreshSession: () => Promise<boolean>;
  user: User | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, setUser, setLoading, getAuthHeader } = useAuthStore();
  const [webSocketService, setWebSocketService] = useState<WebSocketService | null>(null);

  useEffect(() => {
    if (user) {
      const wsService = new WebSocketService(getAuthHeader);
      wsService.connect(user).then(() => {
        setWebSocketService(wsService);
      }).catch(console.error);

      return () => {
        wsService.close();
      };
    } else {
      setWebSocketService(null);
    }
  }, [user, getAuthHeader]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const handleAuthChange = async (user: User | null) => {
        await setUser(user);
        setLoading(false);
      };
  
      const unsubscribe = onAuthStateChanged(auth, handleAuthChange);
  
      return () => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      };
    }
  }, [setUser, setLoading]);
  

  const login = async (email: string, password: string): Promise<boolean> => {
    setLoading(true);
    console.log("Login function called");
    try {
      console.log("Attempting to sign in with Firebase");
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      console.log("Firebase authentication successful");

      const idToken = await userCredential.user.getIdToken();
      console.log("Got ID token from Firebase");
      console.log("Sending token to backend");
      const response = await fetch(`${API_URL}/api/v1/login`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${idToken}`
          },
          credentials: 'include', // Important for including cookies in the request
        });

        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`Login failed: ${response.status} ${errorData}`);
        }
        console.log("Response status:", response.status);  
        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`Login failed: ${response.status} ${errorData}`);
        }
        
        const data = await response.json();
        setLoading(false);
        await setUser(userCredential.user);
        document.cookie = `session_id=${data.session_id}; path=/; max-age=3600; SameSite=Lax`;
        return true;
      } catch (error) {
        console.error('Login error:', error);
        setLoading(false);
        return false;
      }
    };

  const register = async (email: string, password: string) => {
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      // The user state will be updated by the onAuthStateChanged listener
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      console.log("Logout initiated");
      const response = await fetch(`${API_URL}/api/v1/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log("Logout response status:", response.status);
      if (!response.ok) {
        throw new Error(`Logout failed: ${response.status}`);
      }
      await signOut(auth);
      await setUser(null);
      console.log("Logout successful");
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  const refreshSession = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/refresh-session`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        // Update any necessary state or tokens
        return true;
      }
    } catch (error) {
      console.error('Failed to refresh session:', error);
    }
    return false;
  };

  const refreshToken = async () => {
    if (auth.currentUser) {
      try {
        const newToken = await auth.currentUser.getIdToken(true);
        const response = await fetch(`${API_URL}/api/v1/refresh-session`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        });
  
        if (response.ok) {
          // Session refreshed successfully
          await setUser(auth.currentUser); // Update user state if needed
          return true;
        } else {
          throw new Error('Failed to refresh session');
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        await logout(); // Force logout on refresh failure
        return false;
      }
    }
    return false;
  };

  return (
    <AuthContext.Provider value={{ login, logout, register, webSocketService, refreshSession, user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
