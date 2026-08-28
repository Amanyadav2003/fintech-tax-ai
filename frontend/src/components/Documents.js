import React, { useEffect, useState } from 'react';
import { CheckCircle2, Download, FileText, Trash2, Upload } from 'lucide-react';
import api from '../services/api';
import { DOCUMENTS } from './DocumentPanel';
import './documents.css';
import LoadingSkeleton from './LoadingSkeleton';

const OTHER_FIELDS = { donations_80g: 'Donation amount (possible 80G)', other_deductions: 'Other deduction amount' };

function Documents({ onApplyValues, reviewSeed }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [draftValues, setDraftValues] = useState({});
  const [confirmed, setConfirmed] = useState({});
  const [categories, setCategories] = useState({});
  const [sectionCategories, setSectionCategories] = useState({});
  const [uploading, setUploading] = useState('');
  const load = () => api.get('documents').then(response => setDocuments(response.data)).catch(() => setError('Unable to load your documents.')).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);
  useEffect(() => { setDraftValues(items => documents.reduce((all, item) => ({ ...all, [item.id]: { ...(items[item.id] || item.extracted_data || {}) } }), {})); setCategories(items => documents.reduce((all, item) => ({ ...all, [item.id]: items[item.id] || item.metadata?.classification?.category || 'other' }), {})); }, [documents]);
  useEffect(() => { if (reviewSeed?.documentId) setDraftValues(previous => ({ ...previous, [reviewSeed.documentId]: { ...(previous[reviewSeed.documentId] || {}), ...reviewSeed.values } })); }, [reviewSeed]);
  const remove = async (id) => { if (!window.confirm('Delete this document?')) return; await api.delete(`documents/${id}`); setDocuments(items => items.filter(item => item.id !== id)); };
  const upload = async (type, file) => {
    if (!file) return;
    setUploading(type); setError('');
    try { const form = new FormData(); form.append('file', file); await api.post(`documents/upload?document_type=${type}`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); await load(); }
    catch (err) { setError(err.response?.data?.detail || 'Upload or extraction failed.'); }
    finally { setUploading(''); }
  };
  const updateValue = (id, key, value) => setDraftValues(previous => ({ ...previous, [id]: { ...(previous[id] || {}), [key]: value } }));
  const apply = () => {
    const values = {};
    documents.forEach(item => {
      if (!confirmed[item.id]) return;
      Object.entries(draftValues[item.id] || {}).forEach(([key, value]) => { if (value !== '' && value != null && Number.isFinite(Number(value))) values[key] = (values[key] || 0) + Number(value); });
    });
    onApplyValues(values);
  };
  const reviewableCount = documents.filter(item => Object.keys(draftValues[item.id] || {}).length).length;
  if (loading) return <section className="documents-page"><LoadingSkeleton lines={4} /></section>;
  return <section className="documents-page"><div className="documents-heading"><div><p className="eyebrow">Secure storage</p><h1>My Documents</h1><p>Upload as many files as you need. Every suggested value stays here until you review and confirm it.</p></div></div>{error && <p className="document-error">{error}</p>}
    <div className="document-upload-grid">{Object.entries(DOCUMENTS).concat([['other', { title: 'Other Documents', fields: OTHER_FIELDS }]]).map(([type, metadata]) => <label className="vault-upload" key={type}><span>{metadata.title}</span><small>{uploading === type ? 'Extracting...' : 'Add PDF, JPG, or PNG'}</small><Upload size={18} /><input type="file" accept="application/pdf,image/jpeg,image/png" disabled={!!uploading} onChange={event => { upload(type, event.target.files?.[0]); event.target.value = ''; }} /></label>)}</div>
    <section className="review-section"><div className="review-heading"><div><p className="eyebrow">One review queue</p><h2>Review extracted values</h2></div><span>{reviewableCount} document{reviewableCount === 1 ? '' : 's'} ready</span></div>
      {documents.map(item => { const metadata = item.document_type === 'other' ? { title: 'Other Documents', fields: OTHER_FIELDS } : DOCUMENTS[item.document_type]; const values = draftValues[item.id] || {}; const sections = item.metadata?.sections || []; const categoryTotal = documents.filter(document => document.document_type === item.document_type).reduce((total, document) => total + Number(draftValues[document.id]?.[Object.keys(metadata?.fields || {})[0]] || 0), 0); return <article className="review-document" key={item.id}><div className="review-document-header"><FileText size={20} /><div><strong>{item.original_filename}</strong><span>{metadata?.title}</span></div><a className="icon-button" href={`${api.defaults.baseURL}/documents/${item.id}/download`} target="_blank" rel="noreferrer" title="View or download"><Download size={17} /></a><button className="icon-button danger-icon" onClick={() => remove(item.id)} title="Delete document"><Trash2 size={17} /></button></div>
        {item.metadata?.classification?.message && <p className="classification-suggestion">AI suggestion: {item.metadata.classification.message} {item.document_type === 'other' && <select value={categories[item.id] || 'other'} onChange={event => setCategories(previous => ({ ...previous, [item.id]: event.target.value }))} aria-label="Suggested category"><option value="other">Leave in Other Documents</option>{Object.entries(DOCUMENTS).map(([key, value]) => <option key={key} value={key}>{value.title}</option>)}</select>}</p>}
        {sections.length > 1 && <div className="section-suggestions"><strong>Likely combined PDF: confirm page sections</strong>{sections.map((section, index) => { const sectionKey = `${item.id}-${index}`; return <label key={sectionKey}>Pages {section.pages.join(', ')}<select value={sectionCategories[sectionKey] || section.suggested_category || 'other'} onChange={event => setSectionCategories(previous => ({ ...previous, [sectionKey]: event.target.value }))} aria-label={`Category for pages ${section.pages.join(', ')}`}><option value="other">Other Documents</option>{Object.entries(DOCUMENTS).map(([key, value]) => <option key={key} value={key}>{value.title}</option>)}</select></label>; })}</div>}
        {item.document_type === '80c' && categoryTotal > 150000 && <div className="document-warning" role="status"><strong>Review this 80C total</strong><p>The combined suggested amount is above the usual Section 80C limit. Check each file and adjust the confirmed value if needed.</p></div>}
        {Object.keys(metadata?.fields || {}).map(key => <label className="review-field" key={key}>{metadata.fields[key]}<input type={key === 'employer_name' ? 'text' : 'number'} value={values[key] ?? ''} onChange={event => updateValue(item.id, key, event.target.value)} placeholder="Enter manually if needed" /></label>)}
        <label className="review-confirm"><input type="checkbox" checked={!!confirmed[item.id]} onChange={event => setConfirmed(previous => ({ ...previous, [item.id]: event.target.checked }))} /> I reviewed these values and confirm they may be applied</label>
      </article>; })}
      {!documents.length && <p className="empty-copy">No documents uploaded yet. You can also enter values manually in the tax forms.</p>}
      <div className="apply-bar"><span>Only checked documents can be applied. Values from multiple files are combined by field.</span><button className="primary-action" disabled={!documents.some(item => confirmed[item.id])} onClick={apply}><CheckCircle2 size={18} /> Apply to Tax Form</button></div>
    </section>
  </section>;
}
export default Documents;
