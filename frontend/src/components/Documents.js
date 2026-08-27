import React, { useEffect, useState } from 'react';
import { Download, FileText, Trash2 } from 'lucide-react';
import api from '../services/api';
import { DOCUMENTS } from './DocumentPanel';
import './documents.css';
import LoadingSkeleton from './LoadingSkeleton';

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const load = () => api.get('documents').then(response => setDocuments(response.data)).catch(() => setError('Unable to load your documents.')).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);
  const remove = async (id) => { if (!window.confirm('Delete this document?')) return; await api.delete(`documents/${id}`); setDocuments(items => items.filter(item => item.id !== id)); };
  if (loading) return <section className="documents-page"><LoadingSkeleton lines={4} /></section>;
  return <section className="documents-page"><div className="documents-heading"><div><p className="eyebrow">Secure storage</p><h1>My Documents</h1><p>Uploaded documents stay linked to your account and are available for review.</p></div></div>{error && <p className="document-error">{error}</p>}{Object.keys(DOCUMENTS).map(type => { const items = documents.filter(item => item.document_type === type); if (!items.length) return null; return <section className="document-group" key={type}><h2>{DOCUMENTS[type].title}</h2><div className="vault-list">{items.map(item => <article className="vault-row" key={item.id}><FileText size={22} /><div><strong>{item.original_filename}</strong><span>{new Date(item.uploaded_at).toLocaleString('en-IN')}</span></div><a className="icon-button" href={`${api.defaults.baseURL}/documents/${item.id}/download`} target="_blank" rel="noreferrer" title="View or download"><Download size={18} /></a><button className="icon-button danger-icon" onClick={() => remove(item.id)} title="Delete document"><Trash2 size={18} /></button></article>)}</div></section>})}{!documents.length && !error && <p className="empty-copy">No documents uploaded yet.</p>}</section>;
}
export default Documents;
