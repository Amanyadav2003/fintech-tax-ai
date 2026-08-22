import React, { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Receipt, Trash2 } from 'lucide-react';
import api from '../services/api';
import './expenseTracker.css';

const categories = ['80C Investment', 'Medical/Insurance', 'Rent', 'Home Loan', 'Donations', 'Other'];
const currentMonth = new Date().toISOString().slice(0, 7);
function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}`; }

function ExpenseTracker({ onBack }) {
  const [expenses, setExpenses] = useState([]); const [error, setError] = useState('');
  const [form, setForm] = useState({ amount: '', category: categories[0], description: '', date: new Date().toISOString().slice(0, 10) });
  const load = () => api.get(`expenses?month=${currentMonth}`).then(response => setExpenses(response.data || [])).catch(() => setError('Unable to load expenses.'));
  useEffect(load, []);
  const totals = useMemo(() => expenses.reduce((result, expense) => ({ ...result, [expense.category]: (result[expense.category] || 0) + Number(expense.amount) }), {}), [expenses]);
  const maxTotal = Math.max(...Object.values(totals), 1);
  const submit = async (event) => { event.preventDefault(); setError(''); try { await api.post('expenses', { ...form, amount: Number(form.amount), date: `${form.date}T00:00:00` }); setForm(prev => ({ ...prev, amount: '', description: '' })); load(); } catch (err) { setError(err.response?.data?.detail || 'Unable to add expense.'); } };
  const remove = async (id) => { await api.delete(`expenses/${id}`); load(); };
  return <section className="expense-page"><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Home</button><div className="expense-heading"><div><p className="eyebrow">Current month</p><h1>Expense Tracker</h1><p>Keep a simple record of expenses relevant to your tax planning.</p></div><div className="expense-total"><span>Total this month</span><strong>{money(expenses.reduce((sum, item) => sum + Number(item.amount), 0))}</strong></div></div>{error && <div className="expense-error">{error}</div>}<div className="expense-layout"><section className="expense-card"><h2><Receipt size={19} /> Add expense</h2><form onSubmit={submit}><label>Amount<input required type="number" min="0.01" step="0.01" value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} /></label><label>Category<select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>{categories.map(category => <option key={category}>{category}</option>)}</select></label><label>Description <span>(optional)</span><input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label><label>Date<input required type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} /></label><button className="primary-action" type="submit">Add expense</button></form></section><section className="expense-card"><h2>Spending by category</h2><div className="expense-bars">{categories.map(category => <div className="expense-bar-row" key={category}><div><span>{category}</span><strong>{money(totals[category])}</strong></div><div className="bar-track"><span style={{ width: `${((totals[category] || 0) / maxTotal) * 100}%` }} /></div></div>)}</div></section></div><section className="expense-card expense-list"><h2>Entries this month</h2>{expenses.length === 0 ? <p className="empty-copy">No expenses recorded this month.</p> : expenses.map(expense => <div className="expense-row" key={expense.id}><div><strong>{expense.category}</strong><span>{new Date(expense.date).toLocaleDateString('en-IN')}{expense.description ? ` · ${expense.description}` : ''}</span></div><strong>{money(expense.amount)}</strong><button aria-label={`Delete ${expense.category} expense`} onClick={() => remove(expense.id)}><Trash2 size={17} /></button></div>)}</section></section>;
}
export default ExpenseTracker;
