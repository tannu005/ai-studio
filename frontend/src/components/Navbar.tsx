'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import { LogOut, FolderKanban, Shield, User, Camera } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { profile, logout } = useAuth();
  const pathname = usePathname();

  if (!profile) return null; // No navbar if not logged in

  const isAdmin = profile.role === 'admin';
  const dashboardLink = isAdmin ? '/admin' : '/user';

  return (
    <header className="nav-header">
      <div className="flex items-center gap-6" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <Link href={dashboardLink} style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Camera className="w-6 h-6 text-indigo-500" style={{ color: 'var(--color-primary)' }} />
          <span className="logo" style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.02em', background: 'var(--gradient-brand)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            TaskHub
          </span>
        </Link>
        
        <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link 
            href={dashboardLink} 
            className={`btn-base`}
            style={{ 
              background: 'none', 
              boxShadow: 'none',
              color: pathname === dashboardLink ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontWeight: pathname === dashboardLink ? '700' : '500'
            }}
          >
            <FolderKanban className="w-4 h-4" />
            Dashboard
          </Link>
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* User profile capsule */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px', 
          padding: '4px 12px', 
          background: 'var(--bg-secondary)', 
          border: '1px solid var(--border-color)', 
          borderRadius: '24px' 
        }}>
          {profile.avatar_url ? (
            <img 
              src={profile.avatar_url} 
              alt={profile.full_name} 
              style={{ width: '24px', height: '24px', borderRadius: '50%' }}
            />
          ) : (
            <div style={{ 
              width: '24px', 
              height: '24px', 
              borderRadius: '50%', 
              background: 'var(--gradient-brand)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#ffffff',
              fontSize: '11px',
              fontWeight: '700'
            }}>
              {profile.full_name.charAt(0).toUpperCase()}
            </div>
          )}
          
          <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
            {profile.full_name.split(' ')[0]}
          </span>

          <span className={`badge badge-${profile.role}`} style={{ fontSize: '10px', padding: '2px 8px' }}>
            {profile.role === 'admin' ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                <Shield className="w-3 h-3" />
                Admin
              </span>
            ) : 'User'}
          </span>
        </div>

        <ThemeToggle />

        <button 
          onClick={logout} 
          className="btn-base btn-secondary" 
          style={{ padding: '8px 12px', borderRadius: '8px' }}
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
export default Navbar;
