import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import './deductionForm.css';
import api from '../services/api';

const formVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

function DeductionForm({ incomeData, onAnalysisComplete, userEmail, documentValues = {} }) {
  const [deductions, setDeductions] = useState({
    investments_80c: '',
    health_insurance_80d: '',
    education_loan_interest_80e: '',
    home_loan_interest_24b: '',
    donations_80g: '',
    rent_paid_80gg: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { if (Object.keys(documentValues).length) setDeductions(previous => ({ ...previous, ...documentValues })); }, [documentValues]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setDeductions(prev => ({ ...prev, [name]: value }));
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        filing_year: 2025,
        tds_paid: 0,
        advance_tax_paid: 0,
        income_data: { ...incomeData },
        deductions_data: {
          investments: parseFloat(deductions.investments_80c) || 0,
          health_insurance: parseFloat(deductions.health_insurance_80d) || 0,
          education_loan_interest: parseFloat(deductions.education_loan_interest_80e) || 0,
          home_loan_interest: parseFloat(deductions.home_loan_interest_24b) || 0,
          donations: parseFloat(deductions.donations_80g) || 0,
          medical_expenses: 0,
          other: parseFloat(deductions.rent_paid_80gg) || 0,
        },
      };

      const response = await api.post('/tax/analyze', payload);
      localStorage.removeItem(`taxmate_income_draft_${userEmail || 'guest'}`);
      onAnalysisComplete(response.data);

    } catch (err) {
      let errorMessage = 'An error occurred during analysis.';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map(d => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join(' | ');
        } else if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else {
            errorMessage = JSON.stringify(err.response.data.detail);
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      className="form-card"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2>Deductions & Investments</h2>
      <p className="subtitle">Provide your tax-saving investments and expenses.</p>

      {error && <div className="error-message">{error}</div>}

      <motion.form onSubmit={handleAnalyze} variants={formVariants} initial="hidden" animate="visible">
        <motion.div className="form-group" variants={itemVariants}>
          <label>80C Investments (PPF, ELSS, etc.)</label>
          <input type="number" name="investments_80c" value={deductions.investments_80c} onChange={handleChange} placeholder="e.g., 150000" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>80D Health Insurance Premium</label>
          <input type="number" name="health_insurance_80d" value={deductions.health_insurance_80d} onChange={handleChange} placeholder="e.g., 25000" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>80E Education Loan Interest</label>
          <input type="number" name="education_loan_interest_80e" value={deductions.education_loan_interest_80e} onChange={handleChange} placeholder="e.g., 50000" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>24b Home Loan Interest</label>
          <input type="number" name="home_loan_interest_24b" value={deductions.home_loan_interest_24b} onChange={handleChange} placeholder="e.g., 200000" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>80G Donations</label>
          <input type="number" name="donations_80g" value={deductions.donations_80g} onChange={handleChange} placeholder="e.g., 10000" />
        </motion.div>
        
        <motion.div className="form-group" variants={itemVariants}>
          <label>80GG Rent Paid (if no HRA)</label>
          <input type="number" name="rent_paid_80gg" value={deductions.rent_paid_80gg} onChange={handleChange} placeholder="e.g., 120000" />
        </motion.div>

        <motion.div variants={itemVariants}>
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? <div className="spinner" /> : 'Analyze My Taxes'}
          </button>
        </motion.div>
      </motion.form>
    </motion.div>
  );
}

export default DeductionForm;
