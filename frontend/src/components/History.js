import React, { useEffect, useState } from 'react';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import api from '../services/api';
import './history.css';

function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}`; }
function History({ onBack, onViewResult }) {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(true);
  useEffect(() => { api.get('tax/history').then(response => setItems(response.data || [])).finally(() => setLoading(false)); }, []);
  return <section className="history-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Home</button><p className="eyebrow">Your records</p><h1>Analysis History</h1><p className="history-intro">Review every completed analysis saved to your account.</p>{loading ? <p>Loading history...</p> : items.length === 0 ? <div className="empty-history"><h2>No analyses yet</h2><p>Your completed tax analyses will appear here.</p></div> : <div className="history-list">{items.map(item => <article className="history-row" key={item.filing_id}><div><strong>{new Date(item.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</strong><span>Risk score {Number(item.audit_risk_score || 0).toFixed(1)}/10</span></div><div><span>Gross income</span><strong>{money(item.gross_income)}</strong></div><div><span>Deductions</span><strong>{money(item.total_deductions)}</strong></div><div><span>Regime</span><strong>{String(item.recommended_regime || 'new').toUpperCase()}</strong></div><div><span>Old / New tax</span><strong>{money(item.tax_old_regime)} / {money(item.tax_new_regime)}</strong></div><div><span>Savings</span><strong className="savings">{money(item.potential_savings)}</strong></div><button className="view-result" onClick={() => onViewResult(item.filing_id)}>View Full Result <ExternalLink size={15} /></button></article>)}</div>}</section>;
}
export default History;
