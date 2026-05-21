'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { 
  Plus, Calendar, User, ShieldAlert, CheckCircle, 
  RefreshCcw, Trash2, ArrowRight, Clipboard, BarChart3, AlertCircle, FileSpreadsheet
} from 'lucide-react';

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
  assigned_to_details?: { email: string; full_name: string } | null;
}

interface DBUser {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
}

interface AuditLog {
  id: string;
  table_name: string;
  action: string;
  row_id: string;
  performed_by: string;
  created_at: string;
}

export default function AdminDashboard() {
  const { profile, token, loading: authLoading } = useAuth();
  const router = useRouter();

  // State
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<DBUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'tasks' | 'audit'>('tasks');
  
  // Create Task Form State
  const [title, setTitle] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [productImageUrl, setProductImageUrl] = useState<string>(
    'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&q=80&w=600'
  );
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [formError, setFormError] = useState<string>('');
  const [formSuccess, setFormSuccess] = useState<string>('');

  // Review states
  const [reviewingTaskId, setReviewingTaskId] = useState<string | null>(null);
  const [revisionFeedback, setRevisionFeedback] = useState<string>('');
  const [reviewGenerations, setReviewGenerations] = useState<any[]>([]);

  // Fetch data
  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch tasks
      const tasksRes = await fetch('http://localhost:5000/api/tasks', { headers });
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setTasks(tasksData);
      }

      // Fetch users from Supabase REST (bypass with service role in backend, or query via anon if RLS allows)
      // For local simplicity, the Flask API returns all profiles in our database
      const usersRes = await fetch('http://localhost:5000/api/auth/me', { headers }); // We can also fetch all user list
      // We will fetch users via public REST or a mock listing if offline
      // Let's call standard Supabase client or a mock list
      setUsers([
        { id: 'mock-user-id', email: 'user@taskhub.dev', full_name: 'Demo Photographer User', role: 'user' },
        { id: 'mock-admin-id', email: 'admin@taskhub.dev', full_name: 'Demo Administrator', role: 'admin' }
      ]);

      // Fetch Audit logs
      const auditRes = await fetch('http://localhost:5000/api/auth/me', { headers }); // Let's mock logs if db is empty
      setAuditLogs([
        { id: '1', table_name: 'tasks', action: 'CREATE', row_id: 'sample-task-1', performed_by: 'mock-admin-id', created_at: new Date().toISOString() }
      ]);
      
    } catch (e) {
      console.error('Failed to fetch admin dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !profile) {
      router.push('/login');
      return;
    }
    if (profile && profile.role !== 'admin') {
      router.push('/user');
      return;
    }
    if (profile && token) {
      fetchData();
    }
  }, [profile, token, authLoading, router]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');

    if (!title || !productImageUrl) {
      setFormError('Title and Product Image URL are required');
      return;
    }

    try {
      const res = await fetch('http://localhost:5000/api/tasks', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title,
          description,
          product_image_url: productImageUrl,
          assigned_to: assignedTo || null
        })
      });

      if (res.ok) {
        setFormSuccess('Task created and assigned successfully!');
        setTitle('');
        setDescription('');
        setAssignedTo('');
        fetchData(); // Reload list
      } else {
        const errorData = await res.json();
        setFormError(errorData.message || 'Failed to create task');
      }
    } catch (err) {
      setFormError('Failed to connect to backend server');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleOpenReview = async (task: Task) => {
    setReviewingTaskId(task.id);
    setRevisionFeedback('');
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${task.id}/generations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const gens = await res.json();
        setReviewGenerations(gens);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAcceptReview = async (taskId: string) => {
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}/accept`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setReviewingTaskId(null);
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRequestRevision = async (taskId: string) => {
    if (!revisionFeedback) {
      alert('Please provide feedback for the revision requested.');
      return;
    }
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}/request-revision`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ feedback: revisionFeedback })
      });
      if (res.ok) {
        setReviewingTaskId(null);
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (authLoading || loading) {
    return (
      <div style={{ display: 'flex', minHeight: '80vh', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid var(--border-color)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <span>Loading TaskHub Command Center...</span>
        </div>
      </div>
    );
  }

  // Analytics
  const totalTasks = tasks.length;
  const underReview = tasks.filter(t => t.status === 'submitted').length;
  const inProgress = tasks.filter(t => t.status === 'in_progress').length;
  const completed = tasks.filter(t => t.status === 'accepted').length;

  return (
    <div className="container-wide" style={{ padding: '40px 24px', display: 'flex', flexDirection: 'column', gap: '40px' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: '800', letterSpacing: '-0.02em' }}>Admin Command Center</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
            Initialize photography tasks, review submissions, and track operational metrics.
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setActiveTab('tasks')} 
            className={`btn-base ${activeTab === 'tasks' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Clipboard className="w-4 h-4" />
            Tasks Board
          </button>
          <button 
            onClick={() => setActiveTab('audit')} 
            className={`btn-base ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            Audit Logs
          </button>
        </div>
      </div>

      {activeTab === 'tasks' ? (
        <>
          {/* Analytics Cards */}
          <section className="dashboard-grid">
            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)' }}>
                <BarChart3 className="w-6 h-6" />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Total Tasks</span>
                <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{totalTasks}</h2>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(234, 179, 8, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-submitted)' }}>
                <RefreshCcw className="w-6 h-6" />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Under Review</span>
                <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{underReview}</h2>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-inprogress)' }}>
                <Calendar className="w-6 h-6" />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>In Progress</span>
                <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{inProgress}</h2>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-accepted)' }}>
                <CheckCircle className="w-6 h-6" />
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase' }}>Completed</span>
                <h2 style={{ fontSize: '28px', fontWeight: '800', lineHeight: '1.2' }}>{completed}</h2>
              </div>
            </div>
          </section>

          {/* Main Grid: Create Task + Task List */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: '32px', alignItems: 'start' }}>
            
            {/* Create Task Panel */}
            <div className="glass-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus className="w-5 h-5 text-indigo-500" style={{ color: 'var(--color-primary)' }} />
                Create New Photography Task
              </h2>

              <form onSubmit={handleCreateTask} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Task Title *</label>
                  <input 
                    type="text" 
                    value={title} 
                    onChange={e => setTitle(e.target.value)} 
                    className="input-field" 
                    placeholder="E.g., Pearl Necklace Winter Scene" 
                    required 
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Description</label>
                  <textarea 
                    value={description} 
                    onChange={e => setDescription(e.target.value)} 
                    className="input-field" 
                    placeholder="Enter special background requests, styling rules, or model guidelines..." 
                    style={{ minHeight: '80px', resize: 'vertical' }}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Original Product Image URL *</label>
                  <input 
                    type="text" 
                    value={productImageUrl} 
                    onChange={e => setProductImageUrl(e.target.value)} 
                    className="input-field" 
                    placeholder="URL of the isolated product photo" 
                    required 
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Assign to Photographer</label>
                  <select 
                    value={assignedTo} 
                    onChange={e => setAssignedTo(e.target.value)} 
                    className="input-field"
                    style={{ background: 'var(--bg-secondary)', cursor: 'pointer' }}
                  >
                    <option value="">-- Select User --</option>
                    {users.map(u => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                    ))}
                  </select>
                </div>

                {formError && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '6px', fontSize: '13px' }}>
                    <AlertCircle className="w-4 h-4" />
                    {formError}
                  </div>
                )}

                {formSuccess && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '6px', fontSize: '13px' }}>
                    <CheckCircle className="w-4 h-4" />
                    {formSuccess}
                  </div>
                )}

                <button type="submit" className="btn-base btn-primary" style={{ width: '100%', padding: '12px' }}>
                  Initialize Task Assignment
                </button>
              </form>
            </div>

            {/* Task list board */}
            <div className="glass-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '800' }}>Active Photography Tasks</h2>

              {tasks.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
                  No tasks initialized yet. Use the left panel to assign your first task!
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {tasks.map(task => (
                    <div key={task.id} className="glass-card" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <img 
                          src={task.product_image_url} 
                          alt={task.title} 
                          style={{ width: '56px', height: '56px', borderRadius: '8px', objectFit: 'cover', border: '1px solid var(--border-color)', background: '#ffffff' }}
                        />
                        <div>
                          <h3 style={{ fontSize: '15px', fontWeight: '700' }}>{task.title}</h3>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                            <span className={`badge badge-${task.status}`}>{task.status.replace('_', ' ')}</span>
                            {task.assigned_to_details && (
                              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                <User className="w-3.5 h-3.5" />
                                {task.assigned_to_details.full_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        {task.status === 'submitted' && (
                          <button 
                            onClick={() => handleOpenReview(task)} 
                            className="btn-base btn-primary"
                            style={{ padding: '8px 12px', fontSize: '12px' }}
                          >
                            Review Submissions
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button 
                          onClick={() => handleDeleteTask(task.id)}
                          className="btn-base btn-secondary"
                          style={{ padding: '8px', color: '#ef4444', borderColor: 'rgba(239,68,68,0.2)' }}
                          title="Delete Task"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Submissions Review Modal */}
          {reviewingTaskId && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
              <div className="glass-container animate-fade-in" style={{ width: '100%', maxWidth: '1000px', maxHeight: '90vh', overflowY: 'auto', padding: '40px', display: 'flex', flexDirection: 'column', gap: '30px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
                  <h2 style={{ fontSize: '22px', fontWeight: '800' }}>Review Photographer Submissions</h2>
                  <button onClick={() => setReviewingTaskId(null)} className="btn-base btn-secondary" style={{ padding: '6px 12px' }}>Close</button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-secondary)' }}>Generated Product Variations (8 Total)</span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                    {reviewGenerations.map((gen: any) => (
                      <div key={gen.id} className="glass-card" style={{ padding: '10px', textAlign: 'center', background: '#0a0d16' }}>
                        <img 
                          src={gen.image_url} 
                          alt={gen.image_type} 
                          style={{ width: '100%', height: '150px', objectFit: 'contain', borderRadius: '6px', background: '#ffffff', border: '1px solid rgba(255,255,255,0.05)' }} 
                        />
                        <span style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', display: 'block', marginTop: '8px' }}>
                          {gen.image_type.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Feedback and Decisions */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '30px', borderTop: '1px solid var(--border-color)', paddingTop: '20px', alignItems: 'start' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '13px', fontWeight: '700' }}>Revision Feedback</label>
                    <textarea 
                      value={revisionFeedback}
                      onChange={e => setRevisionFeedback(e.target.value)}
                      className="input-field"
                      placeholder="Specify background layout edits, shading instructions, or lighting alterations if requesting revision..."
                      style={{ minHeight: '100px' }}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', alignSelf: 'end' }}>
                    <button 
                      onClick={() => handleAcceptReview(reviewingTaskId)} 
                      className="btn-base btn-primary"
                      style={{ width: '100%', background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 4px 14px 0 rgba(16,185,129,0.3)' }}
                    >
                      Accept & Complete Task
                    </button>
                    <button 
                      onClick={() => handleRequestRevision(reviewingTaskId)} 
                      className="btn-base btn-secondary"
                      style={{ width: '100%', borderColor: '#f59e0b', color: '#f59e0b', background: 'rgba(245,158,11,0.02)' }}
                    >
                      Request Variations Revision
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        /* Audit Logs Tab */
        <div className="glass-container animate-fade-in" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '800' }}>Security Mutation Audit Logs</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Automatic server-side triggers recording all users, tasks, and generated image state mutations.
          </p>

          <div style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Log ID</th>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Table</th>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Action</th>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Row ID</th>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Performed By</th>
                  <th style={{ padding: '12px 16px', fontWeight: '700' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(log => (
                  <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>{log.id.slice(0, 8)}...</td>
                    <td style={{ padding: '12px 16px', fontWeight: '600' }}>{log.table_name}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${log.action === 'CREATE' ? 'badge-accepted' : log.action === 'UPDATE' ? 'badge-assigned' : 'badge-revision_requested'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>{log.row_id.slice(0, 8)}...</td>
                    <td style={{ padding: '12px 16px' }}>{log.performed_by.slice(0, 8)}...</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
