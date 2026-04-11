import React, { useState, useEffect } from 'react';
import { materialsAPI, sprintsAPI, tasksAPI } from '../services/api';
import Mermaid from '../components/Mermaid';

// ─── Tab Button ────────────────────────────────────────────────────────────
const TabBtn = ({ id, label, icon, active, onClick }) => (
  <button
    onClick={() => onClick(id)}
    style={{
      padding: '8px 18px',
      borderRadius: '8px',
      border: 'none',
      cursor: 'pointer',
      fontWeight: '600',
      fontSize: '13px',
      transition: 'all 0.2s',
      background: active ? 'var(--blue)' : 'transparent',
      color: active ? '#fff' : 'var(--gray-500)',
    }}
  >
    {icon} {label}
  </button>
);

// ─── Quiz Component ─────────────────────────────────────────────────────────
const QuizMode = ({ questions }) => {
  const [idx, setIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState({ right: 0, wrong: 0 });
  const [finished, setFinished] = useState(false);

  if (!questions || questions.length === 0)
    return <p className="empty-text">No questions available for quiz.</p>;

  const total = questions.length;

  const handleAnswer = (correct) => {
    setScore(s => ({ ...s, right: s.right + (correct ? 1 : 0), wrong: s.wrong + (correct ? 0 : 1) }));
    if (idx + 1 >= total) { setFinished(true); return; }
    setIdx(i => i + 1);
    setRevealed(false);
  };

  const restart = () => { setIdx(0); setRevealed(false); setScore({ right: 0, wrong: 0 }); setFinished(false); };

  if (finished) {
    const pct = Math.round((score.right / total) * 100);
    const grade = pct >= 80 ? { label: 'Excellent!', color: 'var(--green)' }
                : pct >= 60 ? { label: 'Good job!', color: 'var(--blue)' }
                : { label: 'Keep studying!', color: 'var(--orange)' };
    return (
      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>
          {pct >= 80 ? '🎉' : pct >= 60 ? '👍' : '📚'}
        </div>
        <div style={{ fontSize: '48px', fontWeight: '800', color: grade.color }}>{pct}%</div>
        <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--gray-800)', margin: '8px 0' }}>{grade.label}</div>
        <div style={{ color: 'var(--gray-500)', marginBottom: '32px' }}>
          {score.right} correct · {score.wrong} incorrect · {total} total
        </div>
        <button className="btn btn-primary" onClick={restart}>Try Again</button>
      </div>
    );
  }

  const q = questions[idx];
  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      {/* Progress bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <span style={{ color: 'var(--gray-500)', fontSize: '13px' }}>Question {idx + 1} of {total}</span>
        <span style={{ color: 'var(--green)', fontSize: '13px', fontWeight: '600' }}>✓ {score.right} · ✗ {score.wrong}</span>
      </div>
      <div style={{ height: '4px', background: 'var(--border-light)', borderRadius: '4px', marginBottom: '32px' }}>
        <div style={{ height: '100%', width: `${((idx) / total) * 100}%`, background: 'var(--blue)', borderRadius: '4px', transition: 'width 0.3s' }} />
      </div>

      {/* Question card */}
      <div style={{ background: 'var(--surface-raised)', borderRadius: 'var(--radius)', padding: '28px', marginBottom: '20px', border: '1px solid var(--border-light)' }}>
        <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--blue-light)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '12px' }}>Question</div>
        <div style={{ fontSize: '17px', fontWeight: '600', color: 'var(--gray-800)', lineHeight: '1.6' }}>{q.question_text}</div>
      </div>

      {/* Answer reveal */}
      {!revealed ? (
        <button className="btn btn-primary" style={{ width: '100%', marginBottom: '12px' }} onClick={() => setRevealed(true)}>
          Reveal Answer
        </button>
      ) : (
        <>
          <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 'var(--radius)', padding: '20px', marginBottom: '20px' }}>
            <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--green)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '8px' }}>Answer</div>
            <div style={{ color: 'var(--gray-700)', lineHeight: '1.6' }}>{q.suggested_answer}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <button className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--red)', border: '1px solid rgba(239,68,68,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)', fontWeight: '600', cursor: 'pointer' }}
              onClick={() => handleAnswer(false)}>✗ Got it wrong</button>
            <button className="btn" style={{ background: 'rgba(16,185,129,0.15)', color: 'var(--green)', border: '1px solid rgba(16,185,129,0.3)', padding: '12px', borderRadius: 'var(--radius-sm)', fontWeight: '600', cursor: 'pointer' }}
              onClick={() => handleAnswer(true)}>✓ Got it right</button>
          </div>
        </>
      )}
    </div>
  );
};

// ─── Sprint Task Modal ───────────────────────────────────────────────────────
const AddToSprintModal = ({ material, onClose }) => {
  const [sprints, setSprints] = useState([]);
  const [selectedSprint, setSelectedSprint] = useState('');
  const [subject, setSubject] = useState('Study');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    sprintsAPI.list({ status: 'active' }).then(r => {
      setSprints(r.data.sprints || r.data || []);
    }).catch(console.error);
  }, []);

  const handleAdd = async () => {
    if (!selectedSprint) return;
    setLoading(true);
    try {
      await tasksAPI.create({
        sprint_id: parseInt(selectedSprint),
        subject,
        description: `Review study material: ${material.filename}`,
        estimated_minutes: 30,
        priority: 'medium',
      });
      setSuccess(true);
      setTimeout(onClose, 1500);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', padding: '32px', width: '400px', border: '1px solid var(--border-light)' }}>
        {success ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div style={{ fontSize: '48px' }}>✅</div>
            <div style={{ fontWeight: '700', color: 'var(--green)', marginTop: '12px' }}>Task added to sprint!</div>
          </div>
        ) : (
          <>
            <h3 style={{ color: 'var(--gray-800)', margin: '0 0 8px 0' }}>Add to Sprint</h3>
            <p style={{ color: 'var(--gray-500)', fontSize: '13px', margin: '0 0 24px 0' }}>Create a study task from <strong>{material.filename}</strong></p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--gray-600)', marginBottom: '6px' }}>SELECT SPRINT</label>
              <select value={selectedSprint} onChange={e => setSelectedSprint(e.target.value)} className="form-input" style={{ width: '100%' }}>
                <option value="">-- Choose active sprint --</option>
                {sprints.map(s => <option key={s.sprint_id} value={s.sprint_id}>{s.name}</option>)}
              </select>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--gray-600)', marginBottom: '6px' }}>SUBJECT</label>
              <input value={subject} onChange={e => setSubject(e.target.value)} className="form-input" style={{ width: '100%' }} placeholder="e.g. Physics, Math..." />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <button className="btn" style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-raised)', color: 'var(--gray-600)', border: '1px solid var(--border-light)', cursor: 'pointer' }} onClick={onClose}>Cancel</button>
              <button className="btn btn-primary" style={{ padding: '10px' }} onClick={handleAdd} disabled={!selectedSprint || loading}>
                {loading ? 'Adding...' : 'Add Task'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ─── File Drop Zone ────────────────────────────────────────────────────────
const FileDropZone = ({ onFileSelect, selectedFile, onClear }) => {
  const [dragging, setDragging] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragging(true);
    else if (e.type === 'dragleave') setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  if (selectedFile) {
    return (
      <div className="upload-preview">
        <div style={{ fontSize: '24px' }}>📄</div>
        <div className="upload-preview-info">
          <span className="upload-filename">{selectedFile.name}</span>
          <span className="upload-filesize">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={onClear} style={{ padding: '4px 8px' }}>✕</button>
      </div>
    );
  }

  return (
    <div 
      className={`upload-dropzone ${dragging ? 'dragging' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => document.getElementById('fileInput').click()}
    >
      <input 
        id="fileInput"
        type="file" 
        accept="application/pdf" 
        style={{ display: 'none' }} 
        onChange={e => onFileSelect(e.target.files[0])} 
      />
      <div className="upload-dropzone-icon">📤</div>
      <div className="upload-dropzone-text">
        <span className="upload-dropzone-title">Click or Drop PDF here</span>
        <span className="upload-dropzone-sub">Maximum file size: 20MB</span>
      </div>
    </div>
  );
};

// ─── Main Page ───────────────────────────────────────────────────────────────
const MaterialsPage = () => {
  const [materials, setMaterials] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [showSprintModal, setShowSprintModal] = useState(false);

  useEffect(() => { fetchMaterials(); }, []);

  const fetchMaterials = async () => {
    setLoadingList(true);
    try { const res = await materialsAPI.list(); setMaterials(res.data); }
    catch (err) { console.error(err); }
    finally { setLoadingList(false); }
  };

  const handleUpload = async (e) => {
    if (e) e.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true); setError('');
    try {
      const res = await materialsAPI.upload(formData);
      setFile(null);
      await fetchMaterials();
      if (res.data.material_id) viewMaterial(res.data.material_id);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload and process PDF.');
    } finally { setUploading(false); }
  };

  const viewMaterial = async (id) => {
    setLoadingDetail(true);
    setActiveTab('summary');
    try { const res = await materialsAPI.get(id); setSelectedMaterial(res.data); }
    catch (err) { console.error(err); }
    finally { setLoadingDetail(false); }
  };

  const sectionTitle = (text, color = 'var(--accent)') => (
    <h4 style={{ color, margin: '0 0 16px 0', fontSize: '13px', fontWeight: '700', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{text}</h4>
  );

  return (
    <div>
      {showSprintModal && selectedMaterial && (
        <AddToSprintModal material={selectedMaterial} onClose={() => setShowSprintModal(false)} />
      )}

      <div className="page-header">
        <div>
          <h2>Study Materials</h2>
          <p>Instantly generate AI insights from your lecture notes and PDFs.</p>
        </div>
      </div>

      <div className="page-body grid-2" style={{ gridTemplateColumns: 'minmax(320px, 1fr) 2fr', alignItems: 'start', gap: '24px' }}>

        {/* ── Left: Upload + Library ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card">
            {sectionTitle('📤 Upload')}
            <div style={{ marginBottom: '16px' }}>
              <FileDropZone onFileSelect={setFile} selectedFile={file} onClear={() => setFile(null)} />
            </div>
            {error && <div className="auth-error" style={{ marginBottom: '16px', padding: '8px' }}>{error}</div>}
            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }} 
              disabled={!file || uploading}
              onClick={handleUpload}
            >
              {uploading ? '⏳ Processing PDF...' : '🚀 Start AI Analysis'}
            </button>
          </div>

          <div className="card">
            {sectionTitle('📚 Your Library')}
            <div style={{ maxHeight: '420px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {loadingList ? (
                <div className="loading"><div className="loading-spinner"></div></div>
              ) : materials.length === 0 ? (
                <p className="empty-text">No materials uploaded yet.</p>
              ) : (
                materials.map(m => (
                  <div key={m.material_id}
                    onClick={() => viewMaterial(m.material_id)}
                    style={{
                      cursor: 'pointer', padding: '12px 14px', borderRadius: 'var(--radius-sm)',
                      border: `1px solid ${selectedMaterial?.material_id === m.material_id ? 'var(--blue)' : 'var(--border-light)'}`,
                      background: selectedMaterial?.material_id === m.material_id ? 'rgba(99,102,241,0.08)' : 'var(--surface-raised)',
                      transition: 'all 0.2s'
                    }}>
                    <div style={{ fontWeight: '600', color: 'var(--gray-800)', fontSize: '13px', marginBottom: '3px' }}>📄 {m.filename}</div>
                    <div style={{ color: 'var(--gray-500)', fontSize: '11px' }}>{new Date(m.uploaded_at).toLocaleString()}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── Right: Detail Panel ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {loadingDetail ? (
            <div className="card" style={{ minHeight: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="loading"><div className="loading-spinner"></div><span style={{ marginLeft: 12 }}>Processing AI insights...</span></div>
            </div>
          ) : !selectedMaterial ? (
            <div className="card" style={{ minHeight: '500px' }}>
              <div className="empty-state">
                <div className="empty-icon">📂</div>
                <div className="empty-title">Select a Document</div>
                <div className="empty-text">Upload a PDF or click one from your library to view its AI-generated summary, mindmap, and study questions.</div>
              </div>
            </div>
          ) : (
            <>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <div style={{ fontWeight: '700', fontSize: '18px', color: 'var(--gray-800)' }}>📄 {selectedMaterial.filename}</div>
                  <div style={{ color: 'var(--gray-500)', fontSize: '12px' }}>{new Date(selectedMaterial.uploaded_at).toLocaleString()}</div>
                </div>
                <button className="btn btn-primary" style={{ fontSize: '13px', padding: '8px 16px' }} onClick={() => setShowSprintModal(true)}>
                  ➕ Add to Sprint
                </button>
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', background: 'var(--surface-raised)', padding: '4px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)', width: 'fit-content' }}>
                <TabBtn id="summary" label="Summary" icon="⚡" active={activeTab === 'summary'} onClick={setActiveTab} />
                <TabBtn id="mindmap" label="Mindmap" icon="🗺" active={activeTab === 'mindmap'} onClick={setActiveTab} />
                <TabBtn id="questions" label="Questions" icon="📝" active={activeTab === 'questions'} onClick={setActiveTab} />
                <TabBtn id="quiz" label="Quiz Me" icon="🧠" active={activeTab === 'quiz'} onClick={setActiveTab} />
              </div>

              {/* Tab Content */}
              <div className="card" style={{ minHeight: '460px' }}>

                {/* ── Summary Tab ── */}
                {activeTab === 'summary' && (
                  <div>
                    {sectionTitle('⚡ TL;DR — Key Takeaways')}
                    {selectedMaterial.summary ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {selectedMaterial.summary.split('\n').filter(l => l.trim()).map((line, i) => (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '14px 16px',
                            background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05))',
                            border: '1px solid rgba(99,102,241,0.2)', borderRadius: 'var(--radius-sm)'
                          }}>
                            <span style={{ color: 'var(--blue)', fontWeight: '700', flexShrink: 0, marginTop: '2px' }}>•</span>
                            <span style={{ color: 'var(--gray-700)', fontSize: '14px', lineHeight: '1.7' }}>
                              {line.replace(/^[•\-]\s*/, '')}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-text">No summary was generated for this file. Try re-uploading it.</p>
                    )}
                  </div>
                )}

                {/* ── Mindmap Tab ── */}
                {activeTab === 'mindmap' && (
                  <div>
                    {sectionTitle('🗺 Interactive Mindmap', 'var(--purple-light, var(--blue-light))')}
                    <div style={{
                      background: 'var(--bg-deep)', borderRadius: 'var(--radius-sm)', padding: '24px',
                      border: '1px solid var(--border-light)', minHeight: '380px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto'
                    }}>
                      {selectedMaterial.mindmap ? (
                        <Mermaid chart={selectedMaterial.mindmap.mermaid_markup} />
                      ) : (
                        <p className="empty-text">No mindmap was generated for this file.</p>
                      )}
                    </div>
                  </div>
                )}

                {/* ── Questions Tab ── */}
                {activeTab === 'questions' && (
                  <div>
                    {sectionTitle(`📝 Study Questions (${selectedMaterial.questions?.length || 0})`, 'var(--green-light, var(--green))')}
                    {selectedMaterial.questions && selectedMaterial.questions.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {selectedMaterial.questions.map((q, idx) => (
                          <div key={q.question_id} style={{
                            borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--green)',
                            background: 'var(--surface-raised)', overflow: 'hidden'
                          }}>
                            <div style={{ padding: '14px 16px', fontWeight: '600', color: 'var(--gray-800)', fontSize: '14px', borderBottom: '1px solid var(--border-light)' }}>
                              Q{idx + 1}: {q.question_text}
                            </div>
                            <div style={{ padding: '12px 16px', color: 'var(--gray-600)', fontSize: '13px', lineHeight: '1.6' }}>
                              <strong style={{ color: 'var(--green)' }}>A:</strong> {q.suggested_answer}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-text">No questions were generated for this file.</p>
                    )}
                  </div>
                )}

                {/* ── Quiz Tab ── */}
                {activeTab === 'quiz' && (
                  <div>
                    {sectionTitle('🧠 Quiz Mode — Test Yourself', 'var(--orange, #f59e0b)')}
                    <QuizMode questions={selectedMaterial.questions} />
                  </div>
                )}

              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MaterialsPage;
