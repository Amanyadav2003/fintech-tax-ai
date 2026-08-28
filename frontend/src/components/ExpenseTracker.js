import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Download, Pencil, Receipt, Trash2 } from 'lucide-react';
import api from '../services/api';
import './expenseTracker.css';
import { containsPanOrAadhaar, PII_FIELD_MESSAGE } from '../utils/piiValidator';
import LoadingSkeleton from './LoadingSkeleton';

const categories = ['80C Investment', 'Medical/Insurance', 'Rent', 'Home Loan', 'Donations', 'Other'];
function datePart(date) {
  const value = new Date(date);
  return Number.isNaN(value.getTime()) ? '' : `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
}
function monthKey(date) { return datePart(date).slice(0, 7); }
function monthLabel(month) {
  const [year, monthNumber] = month.split('-');
  return new Date(Number(year), Number(monthNumber) - 1, 1).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
}
export function formatExportDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return [String(date.getDate()).padStart(2, '0'), String(date.getMonth() + 1).padStart(2, '0'), date.getFullYear()].join('-');
}
export function createExpenseCsv(expenses) {
  const escape = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const rows = expenses.map(expense => [expense.amount, expense.category, expense.description || '', formatExportDate(expense.date)].map(escape).join(','));
  return `\uFEFF${['amount,category,description,date', ...rows].join('\r\n')}`;
}
const currentMonth = monthKey(new Date());
function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}`; }

function ExpenseTracker({ onBack }) {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [form, setForm] = useState({ amount: '', category: categories[0], description: '', date: new Date().toISOString().slice(0, 10) });

  const load = () => api.get(`expenses?month=${currentMonth}`).then(response => setExpenses(response.data || [])).catch(() => setError('Unable to load expenses.')).finally(() => setLoading(false));
  useEffect(load, []);
  const totals = useMemo(() => expenses.reduce((result, expense) => ({ ...result, [expense.category]: (result[expense.category] || 0) + Number(expense.amount) }), {}), [expenses]);
  const maxTotal = Math.max(...Object.values(totals), 1);

  const resetForm = () => {
    setEditingId(null);
    setForm(prev => ({ ...prev, amount: '', description: '' }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    if (containsPanOrAadhaar(form.description)) { setError(PII_FIELD_MESSAGE); return; }
    try {
      const payload = { ...form, amount: Number(form.amount), date: `${form.date}T00:00:00` };
      await api.post('expenses', payload);
      if (editingId) await api.delete(`expenses/${editingId}`);
      await load();
      resetForm();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to save expense.');
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`expenses/${id}`);
      setExpenses(previous => previous.filter(expense => expense.id !== id));
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to delete expense.');
    }
  };

  const loadHistory = async () => {
    setError('');
    try {
      const response = await api.get('expenses');
      const months = [...new Set((response.data || []).map(expense => monthKey(expense.date)).filter(month => month && month < currentMonth))].sort().reverse();
      setHistory(months);
      setShowHistory(true);
    } catch (err) {
      setError('Unable to load expense history.');
    }
  };

  const exportCsv = async (month = currentMonth, monthExpenses = expenses) => {
    let rowsToExport = monthExpenses;
    if (month !== currentMonth) {
      const response = await api.get(`expenses?month=${month}`);
      rowsToExport = response.data || [];
    }
    const blob = new Blob([createExpenseCsv(rowsToExport)], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `TaxMate_Expenses_${monthLabel(month).replace(' ', '_')}.csv`; link.click(); URL.revokeObjectURL(link.href);
  };

  const edit = (expense) => {
    setEditingId(expense.id);
    setForm({ amount: String(expense.amount), category: expense.category, description: expense.description || '', date: new Date(expense.date).toISOString().slice(0, 10) });
    setError('');
  };

  if (loading) return <section className="expense-page"><LoadingSkeleton lines={5} /></section>;
  return <section className="expense-page">
    <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Home</button>
    <div className="expense-heading"><div><p className="eyebrow">Current month</p><h1>Expense Tracker</h1><p>Keep a simple record of expenses relevant to your tax planning.</p></div><div className="expense-total"><span>Total this month</span><strong>{money(expenses.reduce((sum, item) => sum + Number(item.amount), 0))}</strong></div></div>
    {error && <div className="expense-error">{error}</div>}
    <div className="expense-layout">
      <section className="expense-card"><h2><Receipt size={19} /> {editingId ? 'Edit expense' : 'Add expense'}</h2><form onSubmit={submit}><label>Amount<input required type="number" min="0.01" step="0.01" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} /></label><label>Category<select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>{categories.map(category => <option key={category}>{category}</option>)}</select></label><label>Description <span>(optional)</span><input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label><label>Date<input required type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} /></label><button className="primary-action" type="submit">{editingId ? 'Save changes' : 'Add expense'}</button>{editingId && <button type="button" className="secondary-action" onClick={resetForm}>Cancel edit</button>}</form></section>
      <section className="expense-card"><h2>Spending by category</h2><div className="expense-bars">{categories.map(category => <div className="expense-bar-row" key={category}><div><span>{category}</span><strong>{money(totals[category])}</strong></div><div className="bar-track"><span style={{ width: `${((totals[category] || 0) / maxTotal) * 100}%` }} /></div></div>)}</div></section>
    </div>
    <section className="expense-card expense-list"><div className="expense-list-heading"><div><h2>Entries this month</h2><span className="expense-month-label">{monthLabel(currentMonth)}</span></div><div className="expense-actions"><button className="secondary-action" onClick={() => exportCsv()} disabled={!expenses.length}><Download size={16} /> Export current month</button><button className="secondary-action" onClick={loadHistory}><Receipt size={16} /> Previous months</button></div></div>{expenses.length === 0 ? <p className="empty-copy">No expenses recorded this month.</p> : expenses.map(expense => <div className="expense-row" key={expense.id}><div><strong>{expense.category}</strong><span>{expense.description || 'No description'} · {new Date(expense.date).toLocaleDateString('en-IN')}</span></div><strong>{money(expense.amount)}</strong><button className="icon-button" onClick={() => edit(expense)} aria-label="Edit expense"><Pencil size={16} /></button><button className="icon-button danger" onClick={() => remove(expense.id)} aria-label="Delete expense"><Trash2 size={16} /></button></div>)}{showHistory && <div className="expense-history"><h3>Expense History</h3>{history.length === 0 ? <p className="empty-copy">No previous month expenses.</p> : history.map(month => <div className="expense-history-row" key={month}><span>{monthLabel(month)}</span><button className="secondary-action" onClick={() => exportCsv(month, [])}><Download size={16} /> Download CSV</button></div>)}</div>}</section>
  </section>;
}

export default ExpenseTracker;
