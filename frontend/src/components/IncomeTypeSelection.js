import React from 'react';
import { ArrowRight, BriefcaseBusiness, Building2, WalletCards } from 'lucide-react';
import './incomeTypeSelection.css';

const incomeTypes = [
  { value: 'Salaried', label: 'Salaried', description: 'Salary, Form 16, HRA and employment income.', icon: WalletCards },
  { value: 'Business', label: 'Business', description: 'Business revenue, professional income and expenses.', icon: Building2 },
  { value: 'Self-employed', label: 'Self-Employed', description: 'Independent professional income and deductions.', icon: BriefcaseBusiness },
];

function IncomeTypeSelection({ onSelect }) {
  return <section className="income-type-selection"><p className="eyebrow">Tax Analysis</p><h1>Choose your income type</h1><p className="income-type-subtitle">We will ask only for information relevant to your selected income type.</p><div className="income-type-options">{incomeTypes.map(({ value, label, description, icon: Icon }) => <button key={value} type="button" className="income-type-option" onClick={() => onSelect(value)}><Icon size={28} aria-hidden="true" /><span><strong>{label}</strong><small>{description}</small></span><ArrowRight size={19} aria-hidden="true" /></button>)}</div></section>;
}

export default IncomeTypeSelection;