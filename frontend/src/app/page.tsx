'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import { Camera, Shield, Zap, Sparkles, ArrowRight, Layers, Image as ImageIcon } from 'lucide-react';

export default function LandingPage() {
  const { profile } = useAuth();
  
  const dashboardLink = profile ? (profile.role === 'admin' ? '/admin' : '/user') : '/login';

  return (
    <div className="container-wide" style={{ padding: '60px 24px', display: 'flex', flexDirection: 'column', gap: '80px' }}>
      {/* Hero Section */}
      <section style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        textAlign: 'center', 
        gap: '24px', 
        marginTop: '40px',
        animation: 'fadeIn 0.6s ease-out' 
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '24px',
          fontSize: '13px',
          fontWeight: '600',
          color: 'var(--color-primary)'
        }}>
          <Sparkles className="w-4 h-4" />
          Next-Gen AI Photography Studio Integrated
        </div>

        <h1 style={{ 
          fontSize: '56px', 
          fontWeight: '800', 
          lineHeight: '1.15', 
          letterSpacing: '-0.03em',
          maxWidth: '850px',
          margin: '10px 0'
        }}>
          Supercharge E-Commerce with <span style={{ background: 'var(--gradient-brand)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Pixel-Perfect AI</span> Photography
        </h1>

        <p style={{ 
          fontSize: '18px', 
          color: 'var(--text-secondary)', 
          maxWidth: '650px', 
          lineHeight: '1.6' 
        }}>
          Assign tasks, extract products flawlessly, and generate stunning photorealistic DSLR studio shots in 8 key configurations with 100% product consistency.
        </p>

        <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
          <Link href={dashboardLink} className="btn-base btn-primary" style={{ padding: '14px 28px', fontSize: '15px' }}>
            Enter TaskHub
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="#features" className="btn-base btn-secondary" style={{ padding: '14px 28px', fontSize: '15px' }}>
            Explore Features
          </Link>
        </div>
      </section>

      {/* Visual Demo Card */}
      <section className="glass-container" style={{ padding: '40px', display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '40px', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 style={{ fontSize: '32px', fontWeight: '800', letterSpacing: '-0.02em' }}>
            Guaranteed Product Consistency
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '16px', lineHeight: '1.6' }}>
            Traditional AI image generation changes product shapes and details. TaskHub is engineered to isolate the product itself, generating 8 custom-composed professional DSLR environments without altering a single pixel of your jewelry or merchandise.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Layers className="w-5 h-5 text-indigo-500" style={{ color: 'var(--color-primary)' }} />
              <strong style={{ fontSize: '14px' }}>Pixel-Perfect Edge Extraction (rembg)</strong>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Sparkles className="w-5 h-5 text-sky-500" style={{ color: 'var(--color-secondary)' }} />
              <strong style={{ fontSize: '14px' }}>8 Predefined Angles & Themes (White, Velvet, Beach, Model)</strong>
            </div>
          </div>
        </div>

        {/* Backdrop Visual Grid Mockup */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: '16px',
          background: 'rgba(0,0,0,0.15)',
          padding: '24px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)'
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '100%', height: '90px', background: '#ffffff', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '10px', color: '#666', fontWeight: '700' }}>White BG</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>E-Commerce</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '100%', height: '90px', background: 'linear-gradient(135deg, #1e1b4b, #312e81)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '10px', color: '#a5b4fc', fontWeight: '700' }}>Luxury Velvet</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Theme BG</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '100%', height: '90px', background: 'linear-gradient(135deg, #78350f, #9a3412)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '10px', color: '#fdba74', fontWeight: '700' }}>Autumn Leaves</span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Creative</span>
          </div>
          
          <div style={{ gridColumn: 'span 3', padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', textAlign: 'center', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)' }}>
              💎 Necklace Product Remains 100% Unaltered Across All Formats
            </span>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h2 style={{ fontSize: '32px', fontWeight: '800' }}>Features Crafted for Excellence</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>A seamless collaboration bridge between Admins and Photographers.</p>
        </div>

        <div className="dashboard-grid">
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
              <Shield className="w-5 h-5" />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Admin Dashboard</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
              Create photo assignments, allocate tasks to users, track status flow, and audit database mutations in real time.
            </p>
          </div>

          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(14, 165, 233, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-secondary)' }}>
              <Camera className="w-5 h-5" />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>AI Product Studio</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
              Interactive workspace for photographers to generate, preview, delete, and finalize white-background, creative themed, and model wearing variations.
            </p>
          </div>

          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-accepted)' }}>
              <Zap className="w-5 h-5" />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Email Notifications</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
              Automatic high-quality email dispatches for Task Assignment, Submission, and Acceptance, notifying all stakeholders instantly.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ 
        borderTop: '1px solid var(--border-color)', 
        paddingTop: '30px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        fontSize: '13px',
        color: 'var(--text-muted)'
      }}>
        <span>&copy; 2026 TaskHub AI Product Studio. All rights reserved.</span>
        <div style={{ display: 'flex', gap: '20px' }}>
          <Link href="/login" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>Sign In</Link>
          <a href="file:///C:/Users/YTANNU/.gemini/antigravity/scratch/taskhub/README.md" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>Documentation</a>
        </div>
      </footer>
    </div>
  );
}
