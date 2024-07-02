// app/contexts/AuthContext.tsx
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';
import { auth } from '../lib/firebase'; // Adjust this import path as needed

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is not defined');
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getAuthHeader: () => Promise<HeadersInit>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== 'undefined') {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return () => {
      if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      };
    }
  }, []);

  const login = async (email: string, password: string) => {
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
      console.log("Login successful:", data);
    
      setUser(userCredential.user);  // Set the user to the Firebase user object
      setLoading(false);
      return data;
      setLoading(false);
    } catch (error) {
      setLoading(false);
      console.error('Login error:', error);
      throw error;
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
      setUser(null);
      console.log("Logout successful");
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };
  const getAuthHeader = async (): Promise<HeadersInit> => {
    const currentUser = auth.currentUser;

    if (!currentUser) {
      throw new Error('User not authenticated');
    }

    try {
      const token = await currentUser.getIdToken();
      return { 'Authorization': `Bearer ${token}` };
    } catch (error) {
      console.error('Error getting ID token:', error);
      throw new Error('Failed to get authentication token');
    }
  };
  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, getAuthHeader }}>
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
