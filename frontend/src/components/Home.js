import React, { useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, FileText, Landmark, Receipt, ShieldCheck } from 'lucide-react';
import api from '../services/api';
import DocumentPanel, { DOCUMENTS } from './DocumentPanel';
import './home.css';
import LoadingSkeleton from './LoadingSkeleton';

const needs = [
  ['Form 16', 'Salary, TDS, and employer details.', FileText],
  ['Bank interest certificates', 'Savings and fixed-deposit interest.', Landmark],
  ['80C investment proofs', 'PPF, ELSS, LIC, EPF, and tuition fees.', Receipt],
  ['80D health receipts', 'Premium receipts for health insurance.', ShieldCheck],
  ['Home loan certificate', 'Interest statement for Section 24(b).', FileText],
  ['Rent receipts', 'Keep these for HRA review.', Receipt],
];

function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}`; }

function Home({ user, onStart, onHistory, onViewResult, onOpenDocuments }) {
  const [data, setData] = useState({ latest: null, recent: [], reminders: [] });
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documentCount, setDocumentCount] = useState(0);
  const [loading, setLoading] = useState(true);
  useEffect(() => { Promise.all([api.get('tax/history'), api.get('tax/dashboard'), api.get('documents')]).then(([history, dashboard, documents]) => { const recent = history.data || []; setData({ latest: recent[0] || null, recent: recent.slice(0, 3), reminders: dashboard.data?.compliance_dashboard?.reminders || [] }); setDocumentCount(new Set((documents.data || []).map(item => item.document_type)).size); }).catch(() => {}).finally(() => setLoading(false)); }, []);
  if (loading) return <section className="home-page"><LoadingSkeleton lines={7} /></section>;
  return <section className="home-page"><div className="home-heading"><div><p className="eyebrow">TaxMate AI</p><h1>Welcome, {user.name || user.email}</h1><p>Keep your filing work organized and ready for the next step.</p></div><button className="primary-action" onClick={onStart}>Start New Analysis <ArrowRight size={18} /></button></div>
    <section className="home-section last-analysis">{data.latest ? <><div><p className="eyebrow">Your last analysis</p><h2>{String(data.latest.recommended_regime || 'new').toUpperCase()} regime recommended</h2><p>Potential savings {money(data.latest.potential_savings)}</p></div><button className="secondary-action" onClick={() => onViewResult(data.latest.filing_id)}>View Details</button></> : <><div><p className="eyebrow">Your first analysis</p><h2>Your tax picture starts here.</h2><p>Enter your income and deductions to see a personalized comparison.</p></div><button className="secondary-action" onClick={onStart}>Begin</button></>}</section>
    <section className="home-section"><div className="section-title"><div><p className="eyebrow">Preparation</p><h2>What You'll Need</h2></div><span>{documentCount} of 6 documents ready</span></div><div className="readiness-track"><span style={{ width: `${(documentCount / 6) * 100}%` }} /></div><div className="needs-grid">{needs.map(([title, text, Icon]) => { const type = Object.keys(DOCUMENTS).find(key => DOCUMENTS[key].title === title); return <button className="need-card" key={title} onClick={() => setSelectedDocument(type)}><Icon size={20} /><h3>{title}</h3><p>{text}</p></button>; })}</div></section>
    <div className="home-columns"><section className="home-section"><div className="section-title"><div><p className="eyebrow">Your workspace</p><h2>Recent Activity</h2></div><button className="text-action" onClick={onHistory}>View History <ArrowRight size={15} /></button></div>{data.recent.length ? <div className="activity-list">{data.recent.map(item => <button key={item.filing_id} className="activity-row" onClick={() => onViewResult(item.filing_id)}><span>{new Date(item.created_at).toLocaleDateString('en-IN')}</span><strong>{String(item.recommended_regime || 'new').toUpperCase()}</strong><span>{money(item.potential_savings)} saved</span></button>)}</div> : <p className="empty-copy">Completed analyses will appear here.</p>}</section><section className="home-section"><div className="section-title"><div><p className="eyebrow">Stay on track</p><h2>Upcoming Deadlines</h2></div><CalendarDays size={20} /></div><div className="deadline-list">{data.reminders.map(reminder => <div key={reminder.id}><strong>{reminder.title}</strong><span>{reminder.due_date}</span><p>{reminder.description}</p></div>)}</div></section></div>
    {selectedDocument && <DocumentPanel documentType={selectedDocument} onClose={() => setSelectedDocument(null)} onOpenVault={() => { setSelectedDocument(null); onOpenDocuments(); }} />}</section>;
}
export default Home;
