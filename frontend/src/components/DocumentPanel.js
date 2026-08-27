import React, { useState } from 'react';
import { FileUp, X, CheckCircle2 } from 'lucide-react';
import api from '../services/api';
import './documentPanel.css';
import './extraction.css';

export const DOCUMENTS = {
  form16: { title: 'Form 16', description: 'Your employer issues Form 16. It summarizes salary, exemptions, and tax deducted at source, helping you report salary and TDS accurately.', fields: { salary: 'Gross salary', tds_deducted: 'TDS deducted', employer_name: 'Employer name' } },
  bank_interest: { title: 'Bank interest certificates', description: 'These certificates show interest earned on savings accounts, fixed deposits, and recurring deposits so interest income is not missed.', fields: { interest: 'Total interest' } },
  '80c': { title: '80C investment proofs', description: 'PPF, ELSS, LIC, EPF, and tuition-fee receipts support eligible Section 80C deductions, subject to the applicable limits.', fields: { investments_80c: 'Total invested' } },
  '80d': { title: '80D health receipts', description: 'Health insurance premium receipts support a Section 80D deduction when the policy and taxpayer meet the applicable rules.', fields: { health_insurance_80d: 'Premium paid' } },
  home_loan: { title: 'Home loan certificate', description: 'The lender certificate identifies interest paid on a qualifying home loan, including the amount relevant to Section 24(b).', fields: { home_loan_interest_24b: 'Interest paid' } },
  rent: { title: 'Rent receipts', description: 'Rent receipts provide a record of annual rent paid and can support an eligible rent-related claim where the rules apply.', fields: { rent_paid_80gg: 'Annual rent paid' } },
};

function DocumentPanel({ documentType, onClose, onUseValues, onOpenVault }) {
  const metadata = DOCUMENTS[documentType];
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [values, setValues] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const chooseFile = (nextFile) => { if (nextFile) { setFile(nextFile); setResult(null); setError(''); } };
  const upload = async () => {
    if (!file) return;
    setLoading(true); setError('');
    try {
      const form = new FormData(); form.append('file', file);
      const response = await api.post(`documents/upload?document_type=${documentType}`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(response.data); setValues(response.data.extracted_data || {});
    } catch (err) { setError(err.response?.data?.detail || 'Upload or extraction failed.'); }
    finally { setLoading(false); }
  };
  return <div className="document-backdrop" role="presentation" onClick={onClose}>
    <section className="document-panel" role="dialog" aria-modal="true" aria-labelledby="document-title" onClick={event => event.stopPropagation()}>
      <div className="document-panel-header"><div><p className="eyebrow">Document support</p><h2 id="document-title">{metadata.title}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close document details"><X size={20} /></button></div>
      <p className="document-description">{metadata.description}</p>
      <div className="document-dropzone" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); chooseFile(event.dataTransfer.files?.[0]); }}>
        <FileUp size={28} /><strong>{file ? file.name : 'Drop a PDF, JPG, or PNG here'}</strong><span>Maximum 5MB. Text extraction uses PDF text parsing or image OCR and may need correction.</span>
        <label className="secondary-action">Choose File<input type="file" accept="application/pdf,image/jpeg,image/png" onChange={event => chooseFile(event.target.files?.[0])} hidden /></label>
      </div>
      {file && !result && <button className="primary-action" onClick={upload} disabled={loading}>{loading ? 'Extracting...' : 'Upload and extract'}</button>}
      {error && <p className="document-error" role="alert">{error}</p>}
      {result && <div className="suggested-values"><div className="suggested-heading"><div><h3>Suggested values - please review</h3><p>{result.extraction_note}</p></div><CheckCircle2 size={20} /></div>{Object.keys(values).length === 0 && <p className="extraction-fallback">We couldn't auto-read this document. Please enter the values manually and review them before using.</p>}{Object.entries(metadata.fields).map(([key, label]) => <label key={key}>{label}<input value={values[key] ?? ''} onChange={event => setValues(previous => ({ ...previous, [key]: event.target.value }))} placeholder="Enter manually if needed" /></label>)}<div className="document-actions"><button className="primary-action" onClick={() => onUseValues(values)}>Use These Values</button><button className="text-action" onClick={onOpenVault}>View previously uploaded {metadata.title}</button></div></div>}
      {!result && <button className="text-action" onClick={onOpenVault}>View previously uploaded {metadata.title}</button>}
    </section>
  </div>;
}
export default DocumentPanel;
