'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';
import { 
  ArrowLeft, Camera, Sparkles, Check, Trash2, 
  Download, Eye, Play, Send, RefreshCw, AlertCircle, EyeOff, CheckCircle2
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
}

interface Generation {
  id: string;
  image_type: string;
  image_url: string;
  prompt_used: string;
  angle: string | null;
}

interface GenerationSlot {
  type: string;
  label: string;
  description: string;
  promptPlaceholder: string;
  defaultPrompt: string;
}

export default function AIStudioPage() {
  const { profile, token, loading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const taskId = params.id as string;

  // Task & Generations state
  const [task, setTask] = useState<Task | null>(null);
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string>('');
  
  // Custom prompt input states per slot
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  
  // Active background jobs polling states
  const [activeJobs, setActiveJobs] = useState<Record<string, { jobId: string; progress: number; status: string }>>({});
  
  // Full-size Preview Modal state
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);
  const [previewImageType, setPreviewImageType] = useState<string>('');

  const pollIntervals = useRef<Record<string, NodeJS.Timeout>>({});

  // 8 Predefined variations slots
  const slots: GenerationSlot[] = [
    { type: 'white_bg', label: 'White Background', description: 'Pure white background, clean e-commerce studio lighting.', promptPlaceholder: 'E.g., high-end pearl jewelry isolated on pure white studio background...', defaultPrompt: 'luxury e-commerce product shot, sharp focus, pure white clean background' },
    { type: 'theme_luxury_velvet', label: 'Theme: Royal Velvet', description: 'Deep royal blue premium velvet surface backdrop.', promptPlaceholder: 'E.g., jewelry draped on dark royal blue velvet wrinkles, dramatic light...', defaultPrompt: 'luxury product placement on deep blue velvet background, satin shadows, dramatic lighting' },
    { type: 'theme_marble_surface', label: 'Theme: Carrara Marble', description: 'Polished white marble countertop with blurred background.', promptPlaceholder: 'E.g., necklace placed flat on high-end marble surface, reflections...', defaultPrompt: 'luxury product shot on white polished marble countertop, soft window light, blurred background' },
    { type: 'creative_beach_sunset', label: 'Creative: Golden Sunset', description: 'Glowing sunset backdrop on warm sand particles.', promptPlaceholder: 'E.g., jewelry lying on sand beach, golden sunset flare, sea bokeh...', defaultPrompt: 'warm golden hour sunset on sandy beach backdrop, magical bokeh light' },
    { type: 'creative_autumn_leaves', label: 'Creative: Autumn Leaves', description: 'Earthy wood floor with floating orange maple leaves.', promptPlaceholder: 'E.g., product on rustic wooden platform surrounded by fall leaves...', defaultPrompt: 'autumn scene, floating orange maple leaves, rustic dark wood platform' },
    { type: 'model_front', label: 'Model: Front Angle', description: 'Natural model skin-tone neck drape, DSLR portrait.', promptPlaceholder: 'E.g., model wearing necklace, front chest view, detailed collarbone...', defaultPrompt: 'high-fashion model wearing necklace, front portrait view, elegant collarbone' },
    { type: 'model_side', label: 'Model: Side Profile', description: '45-degree model profile close up landscape.', promptPlaceholder: 'E.g., elegant model side neck profile, soft sunlight...', defaultPrompt: 'beautiful model wearing necklace side profile view, elegant shoulders, detailed ear' },
    { type: 'model_closeup', label: 'Model: Close-Up View', description: 'Collarbone close-up rendering, fine detailing.', promptPlaceholder: 'E.g., close up collarbone portrait, intricate reflections...', defaultPrompt: 'ultra close up detailed view of collarbone, high quality skin texture' }
  ];

  const fetchTaskDetails = async () => {
    if (!token) return;
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch task info
      const taskRes = await fetch(`http://localhost:5000/api/tasks/${taskId}`, { headers });
      if (taskRes.ok) {
        const taskData = await taskRes.json();
        setTask(taskData);
      } else {
        setErrorMessage('Failed to fetch task details.');
      }

      // Fetch generations
      const gensRes = await fetch(`http://localhost:5000/api/tasks/${taskId}/generations`, { headers });
      if (gensRes.ok) {
        const gensData = await gensRes.json();
        setGenerations(gensData);
      }
    } catch (e) {
      console.error(e);
      setErrorMessage('Network connection error.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !profile) {
      router.push('/login');
      return;
    }
    if (profile && token) {
      fetchTaskDetails();
    }
    
    // Cleanup polling intervals on unmount
    return () => {
      Object.values(pollIntervals.current).forEach(clearInterval);
    };
  }, [profile, token, authLoading, taskId]);

  const handleStartTask = async () => {
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}/start`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchTaskDetails();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerGeneration = async (slotType: string) => {
    setErrorMessage('');
    const prompt = customPrompts[slotType] || '';
    
    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_type: slotType,
          prompt_used: prompt
        })
      });

      if (res.status === 202) {
        const data = await res.json();
        const jobId = data.job_id;
        
        // Add to active jobs and start polling
        setActiveJobs(prev => ({
          ...prev,
          [slotType]: { jobId, progress: 10, status: 'pending' }
        }));
        
        startPollingJob(jobId, slotType);
      } else {
        const err = await res.json();
        setErrorMessage(err.message || 'AI Generation rate limit exceeded (10 generations/hour).');
      }
    } catch (e) {
      setErrorMessage('Failed to trigger generation.');
    }
  };

  const startPollingJob = (jobId: string, slotType: string) => {
    // Clear existing interval if any
    if (pollIntervals.current[slotType]) {
      clearInterval(pollIntervals.current[slotType]);
    }

    pollIntervals.current[slotType] = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:5000/api/jobs/${jobId}/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          const job = await res.json();
          
          if (job.status === 'completed') {
            clearInterval(pollIntervals.current[slotType]);
            delete pollIntervals.current[slotType];
            
            // Remove from active jobs
            setActiveJobs(prev => {
              const updated = { ...prev };
              delete updated[slotType];
              return updated;
            });
            
            // Reload generations
            fetchTaskDetails();
          } else if (job.status === 'failed') {
            clearInterval(pollIntervals.current[slotType]);
            delete pollIntervals.current[slotType];
            
            setActiveJobs(prev => {
              const updated = { ...prev };
              delete updated[slotType];
              return updated;
            });
            setErrorMessage(`AI Generation slot ${slotType.replace('_', ' ')} failed: ${job.error}`);
          } else {
            // Update progress
            setActiveJobs(prev => ({
              ...prev,
              [slotType]: { jobId, progress: job.progress, status: job.status }
            }));
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 1500);
  };

  const handleDeleteGeneration = async (genId: string) => {
    if (!confirm('Are you sure you want to delete this generated backdrop variation?')) return;
    try {
      const res = await fetch(`http://localhost:5000/api/generations/${genId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchTaskDetails();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSubmitTask = async () => {
    if (generations.length < 8) {
      alert(`You must finalize all 8 required image configurations. Found ${generations.length}/8.`);
      return;
    }

    try {
      const res = await fetch(`http://localhost:5000/api/tasks/${taskId}/submit`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        fetchTaskDetails();
        alert('Congratulations! Your 8 product photography variations have been submitted to the Admin.');
      } else {
        const err = await res.json();
        alert(err.message || 'Submission failed.');
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
          <span>Loading Photography Studio...</span>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="container-wide" style={{ padding: '60px 24px', textAlign: 'center' }}>
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" style={{ margin: '0 auto 16px' }} />
        <h2>Access Denied or Task Not Found</h2>
        <button onClick={() => router.back()} className="btn-base btn-secondary" style={{ marginTop: '20px' }}>Go Back</button>
      </div>
    );
  }

  const isUser = profile?.role === 'user';
  const isStarted = task.status !== 'assigned';
  const isFinalizedCount = generations.length;
  const isCompleteSubmit = isFinalizedCount === 8;

  return (
    <div className="container-wide" style={{ padding: '30px 24px', display: 'flex', flexDirection: 'column', gap: '30px' }}>
      
      {/* Workspace Header navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <button onClick={() => router.back()} className="btn-base btn-secondary">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '600' }}>Task Status:</span>
          <span className={`badge badge-${task.status}`}>{task.status.replace('_', ' ')}</span>
        </div>
      </div>

      {/* Main Studio Workspace Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2.2fr', gap: '32px', alignItems: 'start' }}>
        
        {/* Left Panel: Original Product details */}
        <div className="glass-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: '800' }}>Original Subject</span>
            <h2 style={{ fontSize: '22px', fontWeight: '800', marginTop: '4px' }}>{task.title}</h2>
          </div>

          <div style={{ width: '100%', height: '260px', borderRadius: '12px', background: '#ffffff', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', overflow: 'hidden' }}>
            <img 
              src={task.product_image_url} 
              alt={task.title} 
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)' }}>Assignment Requirements:</span>
            <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6' }}>
              {task.description || 'Extract the product cleanly and generate all 8 required professional DSLR studio variations. Make sure the lighting shadows and detail projections remain exactly identical.'}
            </p>
          </div>

          {/* Revision feedback note */}
          {task.status === 'revision_requested' && task.revision_notes && (
            <div style={{ padding: '16px', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', color: 'var(--color-revision)', textTransform: 'uppercase' }}>Revision Instructions</span>
              <p style={{ fontSize: '13px', fontStyle: 'italic', color: 'var(--text-primary)' }}>"{task.revision_notes}"</p>
            </div>
          )}

          {/* Studio Controls based on Status */}
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
            {task.status === 'assigned' && isUser ? (
              <button onClick={handleStartTask} className="btn-base btn-primary" style={{ width: '100%', padding: '14px' }}>
                <Play className="w-4 h-4" />
                Initialize AI Studio Workspace
              </button>
            ) : task.status === 'in_progress' || task.status === 'revision_requested' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Progress bar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '700' }}>
                    <span>Variation Finalized Progress</span>
                    <span style={{ color: isCompleteSubmit ? 'var(--color-accepted)' : 'var(--text-secondary)' }}>
                      {isFinalizedCount} / 8 completed
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${(isFinalizedCount / 8) * 100}%`, height: '100%', background: isCompleteSubmit ? 'var(--gradient-brand)' : 'var(--color-primary)', transition: 'width 0.3s ease' }}></div>
                  </div>
                </div>

                {isUser && (
                  <button 
                    onClick={handleSubmitTask} 
                    className="btn-base btn-primary" 
                    style={{ 
                      width: '100%', 
                      padding: '14px', 
                      background: isCompleteSubmit ? 'var(--gradient-brand)' : 'var(--bg-secondary)', 
                      opacity: isCompleteSubmit ? 1 : 0.6,
                      cursor: isCompleteSubmit ? 'pointer' : 'not-allowed',
                      boxShadow: isCompleteSubmit ? '0 4px 14px 0 rgba(99,102,241,0.35)' : 'none'
                    }}
                    disabled={!isCompleteSubmit}
                  >
                    <Send className="w-4 h-4" />
                    Submit Finalized Variations
                  </button>
                )}
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-accepted)', padding: '12px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '8px', fontSize: '13px' }}>
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <span>Task has been submitted to the Admin. Open to edits once revision requested.</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: AI Generation slots */}
        <div className="glass-container" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '800' }}>Product Photography Studio Canvas</h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>* Product details remain 100% pixel-identical</span>
          </div>

          {errorMessage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: '8px', fontSize: '13px' }}>
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {errorMessage}
            </div>
          )}

          {!isStarted ? (
            <div style={{ padding: '100px 40px', textAlign: 'center', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              <Camera className="w-12 h-12 text-indigo-500/30" style={{ color: 'rgba(99,102,241,0.2)' }} />
              <span>Please click "Initialize AI Studio Workspace" on the left panel to begin your assignments.</span>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
              {slots.map(slot => {
                // Check if a final image exists for this slot
                const matchedGen = generations.find(g => g.image_type === slot.type);
                const activeJob = activeJobs[slot.type];
                
                return (
                  <div key={slot.type} className="glass-card animate-fade-in" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', background: 'rgba(0,0,0,0.1)' }}>
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: '700' }}>{slot.label}</h3>
                      <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>{slot.description}</p>
                    </div>

                    {/* Content Area */}
                    <div style={{ width: '100%', height: '200px', borderRadius: '8px', background: '#0a0d16', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
                      {matchedGen ? (
                        /* Generated image preview */
                        <>
                          <img 
                            src={matchedGen.image_url} 
                            alt={slot.label} 
                            style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#ffffff' }}
                          />
                          
                          {/* Image controls overlay */}
                          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)', opacity: 0 }} className="image-hover-overlay">
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button 
                                onClick={() => { setPreviewImageUrl(matchedGen.image_url); setPreviewImageType(slot.label); }} 
                                className="btn-base btn-secondary" 
                                style={{ padding: '6px', borderRadius: '6px', background: 'rgba(255,255,255,0.9)', color: '#000' }}
                                title="Zoom View"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <a 
                                href={matchedGen.image_url} 
                                download={`variation_${slot.type}.png`}
                                className="btn-base btn-secondary" 
                                style={{ padding: '6px', borderRadius: '6px', background: 'rgba(255,255,255,0.9)', color: '#000' }}
                                title="Download File"
                              >
                                <Download className="w-4 h-4" />
                              </a>
                              {(task.status === 'in_progress' || task.status === 'revision_requested') && isUser && (
                                <button 
                                  onClick={() => handleDeleteGeneration(matchedGen.id)} 
                                  className="btn-base btn-secondary" 
                                  style={{ padding: '6px', borderRadius: '6px', background: 'rgba(239,68,68,0.9)', color: '#ffffff', border: 'none' }}
                                  title="Delete & Regenerate"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        </>
                      ) : activeJob ? (
                        /* Generation active loading progress */
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', padding: '20px', textAlign: 'center' }}>
                          <div style={{ 
                            width: '32px', 
                            height: '32px', 
                            border: '3px solid var(--border-color)', 
                            borderTopColor: 'var(--color-primary)', 
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite'
                          }}></div>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600' }}>
                            Composing backdrop... {activeJob.progress}%
                          </span>
                        </div>
                      ) : (
                        /* Setup input & trigger controls */
                        <div style={{ padding: '24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                          <Sparkles className="w-8 h-8 text-indigo-500/20" style={{ color: 'rgba(99,102,241,0.1)' }} />
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Variation Not Composed</span>
                          {(task.status === 'in_progress' || task.status === 'revision_requested') && isUser && (
                            <button 
                              onClick={() => handleTriggerGeneration(slot.type)} 
                              className="btn-base btn-secondary"
                              style={{ fontSize: '11px', padding: '6px 12px', borderColor: 'var(--color-primary)' }}
                            >
                              Generate backdrop
                            </button>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Prompt configuration input slot (only visible when image is missing and task editable) */}
                    {!matchedGen && !activeJob && (task.status === 'in_progress' || task.status === 'revision_requested') && isUser && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input 
                          type="text" 
                          value={customPrompts[slot.type] || ''}
                          onChange={e => setCustomPrompts(prev => ({ ...prev, [slot.type]: e.target.value }))}
                          className="input-field"
                          placeholder={slot.promptPlaceholder}
                          style={{ fontSize: '11px', padding: '8px 12px' }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>

      {/* Full-size Image Preview Modal overlay */}
      {previewImageUrl && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', maxWidth: '700px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#ffffff' }}>
              <span style={{ fontSize: '14px', fontWeight: '700' }}>{previewImageType}</span>
              <button 
                onClick={() => setPreviewImageUrl(null)} 
                style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer', fontWeight: '700', fontSize: '14px' }}
              >
                Close Zoom [X]
              </button>
            </div>
            
            <div style={{ width: '100%', height: '550px', background: '#ffffff', borderRadius: '12px', overflow: 'hidden', padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img 
                src={previewImageUrl} 
                alt="Zoomed Studio Render" 
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Embedded inline hover styles workaround for Next.js app directory styling */}
      <style dangerouslySetInnerHTML={{__html: `
        .image-hover-overlay {
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.2s ease;
        }
        .image-hover-overlay:hover {
          opacity: 1 !important;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}} />
    </div>
  );
}
