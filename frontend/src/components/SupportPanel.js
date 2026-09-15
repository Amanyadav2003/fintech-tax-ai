import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import './support.css';

const categories = ['Tax Calculation', 'Tax Regime', 'Deduction', 'Document Upload', 'Filing Question', 'Account/Login Assistance', 'Technical Issue', 'Other'];
const statuses = ['Open', 'In Progress', 'Resolved'];

function formatDate(value) {
  return value ? new Date(value).toLocaleString('en-IN') : '';
}

function TicketConversation({ ticket, adminMode, onBack, onRefresh }) {
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState(ticket.status);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const sendMessage = async () => {
    if (!message.trim()) return;
    setSending(true);
    setError('');
    try {
      const path = adminMode ? `support/admin/tickets/${ticket.id}/messages` : `support/tickets/${ticket.id}/messages`;
      await api.post(path, { message: message.trim() });
      setMessage('');
      await onRefresh();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to send your message.');
    } finally {
      setSending(false);
    }
  };

  const updateStatus = async (event) => {
    const nextStatus = event.target.value;
    setStatus(nextStatus);
    setError('');
    try {
      await api.patch(`support/admin/tickets/${ticket.id}/status`, { status: nextStatus });
      await onRefresh();
    } catch (err) {
      setStatus(ticket.status);
      setError(err.response?.data?.detail || 'Unable to update ticket status.');
    }
  };

  return <div className="support-detail">
    <button type="button" className="support-back" onClick={onBack}>Back to tickets</button>
    <div className="support-ticket-heading"><div><span className="support-ticket-code">{ticket.ticket_code}</span><h4>{ticket.subject}</h4><small className="support-detail-meta">{ticket.category} · Created {formatDate(ticket.created_at)}</small></div><span className={`support-status status-${ticket.status.toLowerCase().replace(' ', '-')}`}>{ticket.status}</span></div>
    {adminMode && ticket.owner && <p className="support-owner">{ticket.owner.name} &lt;{ticket.owner.email}&gt;</p>}
    <p className="support-description">{ticket.description}</p>
    {adminMode && <label className="support-field">Status<select value={status} onChange={updateStatus}>{statuses.map(value => <option key={value}>{value}</option>)}</select></label>}
    <div className="support-messages">{ticket.messages?.length ? ticket.messages.map(item => <article className={`support-message ${item.sender_type}`} key={item.id}><div><strong>{item.sender_type === 'support' ? 'Support' : 'You'}</strong><time>{formatDate(item.created_at)}</time></div><p>{item.message}</p></article>) : <p className="support-empty">No replies yet.</p>}</div>
    {error && <p className="support-error" role="alert">{error}</p>}
    <label className="support-field">{adminMode ? 'Reply to user' : 'Add a reply'}<textarea value={message} maxLength="5000" onChange={event => setMessage(event.target.value)} placeholder="Write your message" /></label>
    <button type="button" className="support-submit" disabled={sending || !message.trim()} onClick={sendMessage}>{sending ? 'Sending...' : 'Send reply'}</button>
  </div>;
}

function SupportPanel() {
  const [tickets, setTickets] = useState([]);
  const [selected, setSelected] = useState(null);
  const [adminMode, setAdminMode] = useState(false);
  const [adminTickets, setAdminTickets] = useState([]);
  const [adminFilter, setAdminFilter] = useState('');
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState(categories[0]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('support/tickets');
      setTickets(response.data || []);
      try {
        const adminResponse = await api.get(`support/admin/tickets${adminFilter ? `?status_filter=${encodeURIComponent(adminFilter)}` : ''}`);
        setAdminMode(true);
        setAdminTickets(adminResponse.data || []);
      } catch {
        setAdminMode(false);
        setAdminTickets([]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load support tickets.');
    } finally {
      setLoading(false);
    }
  }, [adminFilter]);

  useEffect(() => { loadTickets(); }, [loadTickets]);

  const openTicket = async (ticket, isAdmin = false) => {
    setError('');
    try {
      const path = isAdmin ? `support/admin/tickets/${ticket.id}` : `support/tickets/${ticket.id}`;
      const response = await api.get(path);
      setSelected({ ...response.data, adminMode: isAdmin });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load this support ticket.');
    }
  };

  const submitTicket = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const response = await api.post('support/tickets', { subject, category, description });
      setSubject('');
      setCategory(categories[0]);
      setDescription('');
      setSuccess(`Ticket ${response.data.ticket_code} was created.`);
      await loadTickets();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to create your support ticket.');
    } finally {
      setSubmitting(false);
    }
  };

  const refreshSelected = async () => {
    if (!selected) return loadTickets();
    const path = selected.adminMode ? `support/admin/tickets/${selected.id}` : `support/tickets/${selected.id}`;
    const response = await api.get(path);
    setSelected({ ...response.data, adminMode: selected.adminMode });
  };

  if (selected) return <TicketConversation ticket={selected} adminMode={selected.adminMode} onBack={() => setSelected(null)} onRefresh={refreshSelected} />;

  return <div className="support-panel">
    <h3>Help &amp; Support</h3>
    <div className="support-faq"><strong>Common questions</strong><details><summary>How is tax calculated?</summary><p>TaxMate AI compares the applicable old and new regime estimates using the information you provide.</p></details><details><summary>Which regime can I choose?</summary><p>The comparison helps you review both regimes before deciding which applies to your situation.</p></details><details><summary>What documents can I upload?</summary><p>Use My Documents for supported tax records and review every extracted value before applying it.</p></details><details><summary>How do I contact support?</summary><p>Email support@taxmate.ai or raise a ticket below.</p></details></div>
    <p className="support-contact">For account or filing questions: <a href="mailto:support@taxmate.ai">support@taxmate.ai</a></p>
    <form className="support-form" onSubmit={submitTicket}><h4>Raise a Support Ticket</h4><label className="support-field">Subject<input value={subject} maxLength="160" required onChange={event => setSubject(event.target.value)} /></label><label className="support-field">Category<select value={category} onChange={event => setCategory(event.target.value)}>{categories.map(value => <option key={value}>{value}</option>)}</select></label><label className="support-field">Question or description<textarea value={description} maxLength="5000" required onChange={event => setDescription(event.target.value)} /></label><button type="submit" className="support-submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Submit ticket'}</button></form>
    {success && <p className="support-success" role="status">{success}</p>}
    {error && <p className="support-error" role="alert">{error}</p>}
    <section className="support-ticket-list"><div className="support-list-heading"><h4>{adminMode ? 'Support Admin Tickets' : 'My Support Tickets'}</h4><div>{adminMode && <select className="support-filter" value={adminFilter} onChange={event => setAdminFilter(event.target.value)}><option value="">All statuses</option>{statuses.map(value => <option key={value}>{value}</option>)}</select>}<button type="button" className="support-refresh" onClick={loadTickets}>Refresh</button></div></div>{loading ? <p className="support-empty">Loading tickets...</p> : (adminMode ? adminTickets : tickets).length === 0 ? <p className="support-empty">No support tickets yet.</p> : (adminMode ? adminTickets : tickets).map(ticket => <button type="button" className="support-ticket-row" key={ticket.id} onClick={() => openTicket(ticket, adminMode)}><span><strong>{ticket.ticket_code}</strong><small>{ticket.subject} · {ticket.category}</small><small>{ticket.description}</small><small>Created {formatDate(ticket.created_at)} · Updated {formatDate(ticket.updated_at)}</small></span><span className={`support-status status-${ticket.status.toLowerCase().replace(' ', '-')}`}>{ticket.status}</span></button>)}</section>
  </div>;
}

export default SupportPanel;
