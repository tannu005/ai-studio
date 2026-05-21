'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../lib/supabase';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string;
  role: 'admin' | 'user';
}

interface AuthContextType {
  user: any;
  profile: UserProfile | null;
  token: string | null;
  loading: boolean;
  loginWithGoogle: () => Promise<void>;
  loginWithGitHub: () => Promise<void>;
  loginWithDemo: (role: 'admin' | 'user') => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  const syncProfile = async (sessionToken: string) => {
    try {
      // Sync user profile with Flask backend
      // First, trigger the sync callback
      await fetch('http://localhost:5000/api/auth/oauth/callback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionToken}`,
          'Content-Type': 'application/json'
        }
      });

      // Then, fetch profile
      const res = await fetch('http://localhost:5000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${sessionToken}`
        }
      });
      
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      } else {
        setProfile(null);
      }
    } catch (e) {
      console.error('Failed to sync profile with backend', e);
      setProfile(null);
    }
  };

  useEffect(() => {
    // Check for demo login
    const savedDemoToken = localStorage.getItem('taskhub_demo_token');
    const savedDemoRole = localStorage.getItem('taskhub_demo_role');

    if (savedDemoToken && savedDemoRole) {
      const mockUser = { id: `mock-${savedDemoRole}-id`, email: `${savedDemoRole}@taskhub.dev` };
      setUser(mockUser);
      setToken(savedDemoToken);
      setProfile({
        id: mockUser.id,
        email: mockUser.email,
        full_name: savedDemoRole === 'admin' ? 'Demo Administrator' : 'Demo Photographer User',
        avatar_url: '',
        role: savedDemoRole as 'admin' | 'user'
      });
      setLoading(false);
      return;
    }

    // Set up standard Supabase Auth Listener
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          setUser(session.user);
          setToken(session.access_token);
          await syncProfile(session.access_token);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setLoading(true);
      if (session) {
        setUser(session.user);
        setToken(session.access_token);
        await syncProfile(session.access_token);
      } else {
        setUser(null);
        setToken(null);
        setProfile(null);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const loginWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
  };

  const loginWithGitHub = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
  };

  const loginWithDemo = (role: 'admin' | 'user') => {
    setLoading(true);
    const demoToken = role === 'admin' ? 'mock-admin-token' : 'mock-user-token';
    localStorage.setItem('taskhub_demo_token', demoToken);
    localStorage.setItem('taskhub_demo_role', role);
    
    const mockUser = { id: `mock-${role}-id`, email: `${role}@taskhub.dev` };
    setUser(mockUser);
    setToken(demoToken);
    setProfile({
      id: mockUser.id,
      email: mockUser.email,
      full_name: role === 'admin' ? 'Demo Administrator' : 'Demo Photographer User',
      avatar_url: '',
      role: role
    });
    setLoading(false);
    
    // Redirect to respective dashboard
    router.push(role === 'admin' ? '/admin' : '/user');
  };

  const logout = async () => {
    setLoading(true);
    localStorage.removeItem('taskhub_demo_token');
    localStorage.removeItem('taskhub_demo_role');
    
    if (token && !token.startsWith('mock')) {
      await supabase.auth.signOut();
    }
    
    setUser(null);
    setToken(null);
    setProfile(null);
    setLoading(false);
    router.push('/');
  };

  return (
    <AuthContext.Provider value={{
      user,
      profile,
      token,
      loading,
      loginWithGoogle,
      loginWithGitHub,
      loginWithDemo,
      logout
    }}>
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
