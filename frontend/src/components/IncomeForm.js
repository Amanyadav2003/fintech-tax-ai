import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './incomeForm.css';

const formVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

function IncomeForm({ onIncomeSubmit }) {
  const [income, setIncome] = useState({
    salary: '',
    interest: '',
    dividend: '',
    rental_income: '',
    professional_fees: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setIncome(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const incomeData = Object.fromEntries(
      Object.entries(income).map(([key, value]) => [key, parseFloat(value) || 0])
    );
    onIncomeSubmit(incomeData);
  };

  return (
    <motion.div 
      className="form-card"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2>Your Income Sources</h2>
      <p className="subtitle">Enter your annual income from various sources for FY 2024-25.</p>

      <motion.form onSubmit={handleSubmit} variants={formVariants} initial="hidden" animate="visible">
        <motion.div className="form-group" variants={itemVariants}>
          <label>Salary Income</label>
          <input type="number" name="salary" value={income.salary} onChange={handleChange} placeholder="e.g., 800000" min="0" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>Interest Income (Savings, FDs)</label>
          <input type="number" name="interest" value={income.interest} onChange={handleChange} placeholder="e.g., 5000" min="0" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>Dividend Income</label>
          <input type="number" name="dividend" value={income.dividend} onChange={handleChange} placeholder="e.g., 10000" min="0" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>Rental Income</label>
          <input type="number" name="rental_income" value={income.rental_income} onChange={handleChange} placeholder="e.g., 0" min="0" />
        </motion.div>

        <motion.div className="form-group" variants={itemVariants}>
          <label>Business & Professional Income</label>
          <input type="number" name="professional_fees" value={income.professional_fees} onChange={handleChange} placeholder="e.g., 0" min="0" />
        </motion.div>

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
