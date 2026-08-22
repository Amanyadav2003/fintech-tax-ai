import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';
import './complianceDashboard.css';

const sectionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45 } }
};

function ComplianceDashboard({ onBack, onNewAnalysis }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [checklistState, setChecklistState] = useState({});
  const [documentsState, setDocumentsState] = useState({});

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const response = await api.get('/tax/dashboard');
        const dashboardData = response.data.compliance_dashboard || response.data;
        setDashboard(dashboardData);

        const checklist = dashboardData.checklist || [];
        const documents = dashboardData.documents || [];
        setChecklistState(Object.fromEntries(checklist.map((item) => [item.id, item.completed])));
        setDocumentsState(
          Object.fromEntries(
            documents.map((item) => [item.id, { uploaded: !!item.uploaded, verified: !!item.uploaded, fileName: '' }])
          )
        );
        setError('');
      } catch (err) {
        setError('Unable to load the compliance dashboard right now.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  const checklistItems = useMemo(() => dashboard?.checklist || [], [dashboard?.checklist]);
  const reminders = dashboard?.reminders || [];
  const documents = dashboard?.documents || [];
  const filingStatus = dashboard?.filing_status || {};
  const tracking = dashboard?.tracking || {};

  const checklistProgress = useMemo(() => {
    if (!checklistItems.length) {
      return 0;
    }

    const completed = checklistItems.filter((item) => checklistState[item.id] ?? item.completed).length;
    return Math.round((completed / checklistItems.length) * 100);
  }, [checklistItems, checklistState]);

  const handleChecklistToggle = (itemId) => {
    setChecklistState((previous) => ({
      ...previous,
      [itemId]: !previous[itemId]
    }));
  };

  const handleDocumentUpload = (documentId, file) => {
    setDocumentsState((previous) => ({
      ...previous,
      [documentId]: {
        uploaded: !!file,
        verified: false,
        fileName: file?.name || ''
      }
    }));
  };

  const handleVerifyDocument = (documentId) => {
    setDocumentsState((previous) => ({
      ...previous,
      [documentId]: {
        ...(previous[documentId] || {}),
        uploaded: true,
        verified: true
      }
    }));
  };

  if (loading) {
    return (
      <div className="compliance-dashboard loading">
        <p>Loading compliance dashboard...</p>
      </div>
    );
  }

  return (
    <motion.div className="compliance-dashboard" initial="hidden" animate="visible" variants={sectionVariants}>
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Tax Compliance Dashboard</p>
          <h1>Stay ahead of filing, verification, and document readiness.</h1>
          <p className="hero-copy">
            Track deadlines, complete the filing checklist, upload supporting documents, and monitor e-filing status in one place.
          </p>
        </div>
        <div className="status-pill">
          <span>{filingStatus.label || 'Not started'}</span>
          <strong>{tracking.completion_percent || 0}% checklist complete</strong>
        </div>
      </div>

      {error && <div className="dashboard-error">{error}</div>}

      <div className="dashboard-grid">
        <motion.section className="dashboard-card summary-card-dashboard" variants={sectionVariants}>
          <div className="card-title-row">
            <h2>Deadline reminders</h2>
            <span className="card-badge">3 items</span>
          </div>
          <div className="reminder-list">
            {reminders.map((reminder) => (
              <div key={reminder.id} className={`reminder-item ${reminder.status || ''}`}>
                <div>
                  <h3>{reminder.title}</h3>
                  <p>{reminder.description}</p>
                </div>
                <div className="reminder-meta">
                  <strong>{reminder.due_date}</strong>
                  <span>{reminder.status}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        <motion.section className="dashboard-card" variants={sectionVariants}>
          <div className="card-title-row">
            <h2>Compliance checklist tracker</h2>
            <span className="card-badge">{checklistProgress}%</span>
          </div>
          <div className="progress-bar">
            <span style={{ width: `${checklistProgress}%` }} />
          </div>
          <div className="checklist-list">
            {checklistItems.map((item) => {
              const isCompleted = checklistState[item.id] ?? item.completed;
              return (
                <label key={item.id} className={`checklist-item ${isCompleted ? 'done' : ''}`}>
                  <input type="checkbox" checked={isCompleted} onChange={() => handleChecklistToggle(item.id)} />
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.detail}</p>
                  </div>
                </label>
              );
            })}
          </div>
        </motion.section>

        <motion.section className="dashboard-card" variants={sectionVariants}>
          <div className="card-title-row">
            <h2>Document upload & verification</h2>
            <span className="card-badge">{tracking.uploaded_documents || 0}/{tracking.required_documents || documents.length} uploaded</span>
          </div>
          <div className="document-list">
            {documents.map((document) => {
              const documentStatus = documentsState[document.id] || { uploaded: !!document.uploaded, verified: false, fileName: '' };
              return (
                <div key={document.id} className="document-item">
                  <div className="document-info">
                    <strong>{document.name}</strong>
                    <p>{document.reason}</p>
                    <span className={`document-tag ${document.required ? 'required' : 'optional'}`}>
                      {document.required ? 'Required' : 'Optional'}
                    </span>
                  </div>
                  <div className="document-actions">
                    <input
                      type="file"
                      onChange={(event) => handleDocumentUpload(document.id, event.target.files?.[0])}
                    />
                    <div className="upload-state">
                      <span>{documentStatus.fileName || (documentStatus.uploaded ? 'Uploaded' : 'No file selected')}</span>
                      <button
                        type="button"
                        className="verify-btn"
                        onClick={() => handleVerifyDocument(document.id)}
                        disabled={!documentStatus.uploaded}
                      >
                        {documentStatus.verified ? 'Verified' : 'Verify'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.section>

        <motion.section className="dashboard-card" variants={sectionVariants}>
          <div className="card-title-row">
            <h2>E-filing status tracking</h2>
            <span className={`card-badge stage-${filingStatus.status || 'draft'}`}>{filingStatus.label || 'Draft'}</span>
          </div>
          <p className="status-copy">{filingStatus.next_action || 'Complete your filing details to continue.'}</p>
          <div className="tracking-steps">
            {(filingStatus.steps || []).map((step) => (
              <div key={step.name} className={`tracking-step ${step.completed ? 'complete' : ''}`}>
                <span />
                <strong>{step.name}</strong>
              </div>
            ))}
          </div>
          <div className="tracking-summary">
            <div>
              <span>Checklist completion</span>
              <strong>{tracking.completion_percent || 0}%</strong>
            </div>
            <div>
              <span>Uploaded documents</span>
              <strong>{tracking.uploaded_documents || 0}</strong>
            </div>
          </div>
        </motion.section>
      </div>

      <div className="dashboard-actions">
        <button type="button" className="secondary-action" onClick={onBack}>Back to analysis</button>
        <button type="button" className="primary-action" onClick={onNewAnalysis}>Start new analysis</button>
      </div>
    </motion.div>
  );
}

export default ComplianceDashboard;