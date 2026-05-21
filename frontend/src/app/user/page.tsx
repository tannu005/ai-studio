'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { ClipboardList, Clock, CheckCircle2, ArrowRight, BookOpen, AlertCircle } from 'lucide-react';
import Link from 'next/link';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'submitted' | 'accepted' | 'revision_requested';
  product_image_url: string;
  assigned_to: string | null;
  created_by: string;
  revision_notes: string | null;
  created_at: string;
}

export default function UserDashboard() {
  const { profile, token, loading: authLoading } = useAuth();
  const router = useRouter();

  // State
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const fetchTasks = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/api/tasks/my-tasks', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (e) {
      console.error('Failed to fetch user tasks', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !profile) {
      router.push('/login');
      return;
    }
    if (profile && profile.role === 'admin') {
      router.push('/admin');
      return;
    }
    if (profile && token) {
      fetchTasks();
    }
  }, [profile, token, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div style={{ display: 'flex', minHeight: '80vh', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid var(--border-color)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <span>Loading Photographer Workspace...</span>
        </div>
      </div>
    );
  }

  // Filter tasks
  const filteredTasks = statusFilter === 'all' 
    ? tasks 
    : tasks.filter(t => t.status === statusFilter);

  // Statistics
  const pendingCount = tasks.filter(t => ['assigned', 'revision_requested'].includes(t.status)).length;
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length;
  const completedCount = tasks.filter(t => t.status === 'accepted').length;

  return (
    <div className="container-wide" style={{ padding: '40px 24px', display: 'flex', flexDirection: 'column', gap: '40px' }}>
      
      {/* Welcome Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: '800', letterSpacing: '-0.02em' }}>
            Photographer Workspace
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Welcome back, {profile?.full_name}! Select an assigned product photography task to open the AI Studio.
          </p>
        </div>
      </div>

      {/* Task Counts Summary */}
      <section className="dashboard-grid">
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-assigned)' }}>
            <ClipboardList className="w-6 h-6" />
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>To Do Assignments</span>
            <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{pendingCount}</h2>
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-inprogress)' }}>
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Active In AI Studio</span>
            <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{inProgressCount}</h2>
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-accepted)' }}>
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Accepted & Done</span>
            <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{completedCount}</h2>
          </div>
        </div>
      </section>

      {/* Todo List Board */}
      <div className="glass-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '800' }}>Your Photography Assignments</h2>
          
          {/* Status Filters */}
          <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-secondary)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            {['all', 'assigned', 'in_progress', 'submitted', 'accepted', 'revision_requested'].map(filter => (
              <button 
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className="btn-base"
                style={{ 
                  padding: '6px 12px', 
                  fontSize: '12px', 
                  background: statusFilter === filter ? 'var(--bg-card)' : 'none',
                  color: statusFilter === filter ? 'var(--text-primary)' : 'var(--text-secondary)',
                  boxShadow: statusFilter === filter ? 'var(--shadow-sm)' : 'none'
                }}
              >
                {filter.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Task Cards Grid */}
        {filteredTasks.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
            No assigned tasks found under the selected filter.
          </div>
        ) : (
          <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))' }}>
            {filteredTasks.map(task => (
              <div key={task.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  
                  {/* Image container */}
                  <div style={{ position: 'relative', width: '100%', height: '180px', borderRadius: '8px', background: '#ffffff', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
                    <img 
                      src={task.product_image_url} 
                      alt={task.title} 
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                    <span className={`badge badge-${task.status}`} style={{ position: 'absolute', top: '10px', right: '10px' }}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: '700' }}>{task.title}</h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {task.description || 'No description provided.'}
                    </p>
                  </div>
                </div>

                {/* Revision Notes Alert */}
                {task.status === 'revision_requested' && task.revision_notes && (
                  <div style={{ display: 'flex', gap: '8px', padding: '10px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '6px', fontSize: '12px', color: 'var(--color-revision)' }}>
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <div>
                      <strong>Revision Required:</strong> {task.revision_notes}
                    </div>
                  </div>
                )}

                <Link href={`/tasks/${task.id}`} className="btn-base btn-primary" style={{ width: '100%', marginTop: '8px' }}>
                  <BookOpen className="w-4 h-4" />
                  Open AI Product Studio
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
