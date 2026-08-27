import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, Info } from 'lucide-react';
import './incomeForm.css';

const formVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const initialIncome = {
  salary: '', interest: '', dividend: '', rental_income: '', professional_fees: '',
  tds_deducted: '', hra_received: '', other_sources: '', short_term_capital_gains: '', long_term_capital_gains: '',
};

const descriptions = {
  salary: 'Annual salary from Form 16 or payslips.', interest: 'Savings account and fixed deposit interest.', dividend: 'Dividends received from shares or funds.', rental_income: 'Net annual rent from property.', professional_fees: 'Business or freelance income.', tds_deducted: 'Tax already withheld by your employer or payer.', hra_received: 'House Rent Allowance received from your employer.', other_sources: 'Gifts, lottery winnings, or other miscellaneous income.', short_term_capital_gains: 'Gains from assets held for a short period.', long_term_capital_gains: 'Gains from assets held for a longer period.',
};

function IncomeField({ name, label, value, onChange }) {
  return <motion.div className="form-group" variants={itemVariants}><label htmlFor={name}>{label} <span className="field-help" title={descriptions[name]} aria-label={descriptions[name]}><Info size={14} /></span></label><input id={name} type="number" name={name} value={value} onChange={onChange} placeholder="e.g., 0" min="0" /></motion.div>;
}

const fieldsByType = {
  Salaried: ['salary', 'hra_received', 'tds_deducted', 'interest', 'other_sources', 'dividend', 'rental_income'],
  Business: ['professional_fees', 'interest', 'dividend', 'rental_income', 'other_sources', 'tds_deducted'],
  'Self-employed': ['professional_fees', 'interest', 'dividend', 'rental_income', 'other_sources', 'tds_deducted'],
};

function IncomeForm({ incomeType, onIncomeSubmit, userEmail, documentValues = {} }) {
  const [income, setIncome] = useState(initialIncome);
  const [mismatchDismissed, setMismatchDismissed] = useState(false);
  const [showCapitalGains, setShowCapitalGains] = useState(false);
  const storageKey = `taxmate_income_draft_${userEmail || 'guest'}`;

  useEffect(() => { if (Object.keys(documentValues).length) setIncome(previous => ({ ...previous, ...documentValues })); }, [documentValues]);

  useEffect(() => { const saved = localStorage.getItem(storageKey); if (saved) { try { setIncome({ ...initialIncome, ...JSON.parse(saved) }); setShowCapitalGains(Boolean(JSON.parse(saved).short_term_capital_gains || JSON.parse(saved).long_term_capital_gains)); } catch { localStorage.removeItem(storageKey); } } }, [storageKey]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setIncome(prev => ({
      ...prev,
      [name]: value
    }));
    if (name === 'salary') setMismatchDismissed(false);
    localStorage.setItem(storageKey, JSON.stringify({ ...income, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const incomeData = Object.fromEntries(
      Object.entries(income).map(([key, value]) => [key, parseFloat(value) || 0])
    );
    onIncomeSubmit(incomeData);
  };

  const sourceSalary = Number(documentValues.salary || 0);
  const enteredSalary = Number(income.salary || 0);
  const salaryMismatch = sourceSalary > 0 && enteredSalary > 0 && Math.abs(sourceSalary - enteredSalary) > Math.max(100, sourceSalary * 0.01);
  const visibleFields = fieldsByType[incomeType] || fieldsByType.Salaried;

  return (
    <motion.div 
      className="form-card"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2>{incomeType} Income Details</h2>
      <p className="subtitle">Enter your annual income from various sources for FY 2025-26 (AY 2026-27).</p>
      <div className="running-total"><span>Total Gross Income</span><strong>₹ {Object.entries(income).filter(([key]) => !['tds_deducted', 'hra_received'].includes(key)).reduce((total, [, value]) => total + (parseFloat(value) || 0), 0).toLocaleString('en-IN')}</strong></div>
      {salaryMismatch && !mismatchDismissed && <div className="document-warning" role="status"><strong>Please confirm your salary</strong><p>Form 16 shows ₹{sourceSalary.toLocaleString('en-IN')} for salary, but you entered ₹{enteredSalary.toLocaleString('en-IN')} - please confirm which is correct.</p><div><button type="button" onClick={() => { setIncome(previous => ({ ...previous, salary: String(sourceSalary) })); setMismatchDismissed(true); }}>Use Form 16 value</button><button type="button" onClick={() => setMismatchDismissed(true)}>Keep entered value</button></div></div>}

      <motion.form onSubmit={handleSubmit} variants={formVariants} initial="hidden" animate="visible">
        {visibleFields.includes('salary') && <IncomeField name="salary" label="Salary Income" value={income.salary} onChange={handleChange} />}
        {visibleFields.includes('professional_fees') && <IncomeField name="professional_fees" label="Business & Professional Income" value={income.professional_fees} onChange={handleChange} />}
        {visibleFields.includes('hra_received') && <IncomeField name="hra_received" label="HRA Received (if applicable)" value={income.hra_received} onChange={handleChange} />}
        {visibleFields.includes('tds_deducted') && <IncomeField name="tds_deducted" label="TDS Already Deducted" value={income.tds_deducted} onChange={handleChange} />}
        {visibleFields.includes('interest') && <IncomeField name="interest" label="Interest Income (Savings, FDs)" value={income.interest} onChange={handleChange} />}
        {visibleFields.includes('dividend') && <IncomeField name="dividend" label="Dividend Income" value={income.dividend} onChange={handleChange} />}
        {visibleFields.includes('rental_income') && <IncomeField name="rental_income" label="Rental Income" value={income.rental_income} onChange={handleChange} />}
        {visibleFields.includes('other_sources') && <IncomeField name="other_sources" label="Income from Other Sources" value={income.other_sources} onChange={handleChange} />}

        <motion.div variants={itemVariants} className="capital-toggle"><button type="button" onClick={() => setShowCapitalGains(value => !value)}><ChevronDown size={18} className={showCapitalGains ? 'rotated' : ''} /> {showCapitalGains ? 'Hide Capital Gains' : '+ Add Capital Gains'}</button></motion.div>
        {showCapitalGains && <div className="capital-section"><IncomeField name="short_term_capital_gains" label="Short-Term Capital Gains" value={income.short_term_capital_gains} onChange={handleChange} /><IncomeField name="long_term_capital_gains" label="Long-Term Capital Gains" value={income.long_term_capital_gains} onChange={handleChange} /></div>}

        <motion.div variants={itemVariants}>
          <button type="submit" className="submit-btn">
            Next: Add Deductions
          </button>
        </motion.div>
      </motion.form>
    </motion.div>
  );
}

export default IncomeForm;
