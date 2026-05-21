'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { Camera, Shield, User, Key } from 'lucide-react';

export default function LoginPage() {
  const { profile, loginWithGoogle, loginWithGitHub, loginWithDemo, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If already logged in, redirect to respective dashboard
    if (profile) {
      router.push(profile.role === 'admin' ? '/admin' : '/user');
    }
  }, [profile, router]);

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '80vh', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
        <div className="flex flex-col items-center gap-4" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            border: '3px solid var(--border-color)', 
            borderTopColor: 'var(--color-primary)', 
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <span style={{ fontSize: '14px', fontWeight: '500' }}>Initializing TaskHub Session...</span>
        </div>
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes spin { to { transform: rotate(360deg); } }
        `}} />
      </div>
    );
  }

  return (
    <div style={{ 
      display: 'flex', 
      minHeight: '85vh', 
      alignItems: 'center', 
      justifyContent: 'center', 
      padding: '24px',
      background: 'radial-gradient(circle at top, rgba(99, 102, 241, 0.05), transparent)'
    }}>
      <div className="glass-container animate-fade-in" style={{ width: '100%', maxWidth: '450px', padding: '40px', display: 'flex', flexDirection: 'column', gap: '30px' }}>
        {/* Header */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '10px' }}>
          <div style={{ 
            width: '48px', 
            height: '48px', 
            borderRadius: '12px', 
            background: 'var(--gradient-brand)', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: '0 4px 14px 0 rgba(99, 102, 241, 0.3)'
          }}>
            <Camera className="w-6 h-6" />
          </div>
          <h2 style={{ fontSize: '26px', fontWeight: '800', letterSpacing: '-0.02em', marginTop: '10px' }}>Welcome to TaskHub</h2>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Sign in to access your photography assignments and studio</p>
        </div>

        {/* OAuth Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <button onClick={loginWithGoogle} className="btn-base btn-secondary" style={{ width: '100%', padding: '12px', display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" style={{ flexShrink: 0 }}>
              <path d="M12.24 10.285V13.4h6.887c-.275 1.565-1.88 4.604-6.887 4.604-4.33 0-7.859-3.578-7.859-8s3.53-8 7.859-8c2.46 0 4.105 1.025 5.047 1.926l2.427-2.334C17.955 2.192 15.34 1 12.24 1 5.92 1 1 5.92 1 12s4.92 11 11.24 11c6.6 0 11-4.65 11-11.2 0-.756-.08-1.333-.18-1.8H12.24z"/>
            </svg>
            Continue with Google
          </button>
          
          <button onClick={loginWithGitHub} className="btn-base btn-secondary" style={{ width: '100%', padding: '12px', display: 'flex', gap: '10px', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" style={{ flexShrink: 0 }}>
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.11.82-.26.82-.577v-2.234c-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.43.372.82 1.102.82 2.222v3.293c0 .319.22.694.825.576C20.565 21.795 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            Continue with GitHub
          </button>
        </div>

        {/* Separator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '12px' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }}></div>
          <span>OR OFFLINE DEMO MODE</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }}></div>
        </div>

        {/* Standalone Demo Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px dashed var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Key className="w-4 h-4 text-amber-500" style={{ color: 'var(--color-submitted)' }} />
            <span style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
              Developer Instant Logins
            </span>
          </div>

          <button onClick={() => loginWithDemo('admin')} className="btn-base btn-primary" style={{ width: '100%', padding: '10px', background: 'linear-gradient(135deg, #4f46e5, #4338ca)' }}>
            <Shield className="w-4 h-4" />
            Sign In as Admin
          </button>

          <button onClick={() => loginWithDemo('user')} className="btn-base btn-secondary" style={{ width: '100%', padding: '10px', borderColor: 'var(--color-primary)', borderStyle: 'solid' }}>
            <User className="w-4 h-4 text-indigo-500" style={{ color: 'var(--color-primary)' }} />
            Sign In as Photographer User
          </button>
        </div>
      </div>
    </div>
  );
}
