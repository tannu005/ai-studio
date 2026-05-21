'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';

export default function AuthCallbackPage() {
  const { profile, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (profile) {
        router.push(profile.role === 'admin' ? '/admin' : '/user');
      } else {
        // Fallback in case profile failed to sync or wasn't loaded
        router.push('/login');
      }
    }
  }, [profile, loading, router]);

  return (
    <div style={{ display: 'flex', minHeight: '80vh', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
        <div style={{ 
          width: '40px', 
          height: '40px', 
          border: '3px solid var(--border-color)', 
          borderTopColor: 'var(--color-primary)', 
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <span style={{ fontSize: '14px', fontWeight: '500' }}>Completing authentication...</span>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin { to { transform: rotate(360deg); } }
      `}} />
    </div>
  );
}
