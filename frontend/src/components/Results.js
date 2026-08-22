import React from 'react';
import { motion } from 'framer-motion';
import './results.css';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.2, delayChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 0.5 } }
};

function Results({ analysis }) {
  if (!analysis) return <p>Loading analysis...</p>;

  const {
    tax_analysis,
    risk_analysis,
    strategy_analysis
  } = analysis;

  return (
    <motion.div 
      className="results-container"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div className="results-header" variants={itemVariants}>
        <h1>Your AI-Powered Tax Report</h1>
        <p>Here are the insights from our intelligent analysis of your financial data.</p>
      </motion.div>

      <motion.div className="summary-card" variants={itemVariants}>
        <h3>Recommended Regime: <span style={{fontWeight: 800}}>{tax_analysis.recommended_regime.toUpperCase()}</span></h3>
        <div className="amount">₹ {Math.abs(tax_analysis.potential_savings).toLocaleString('en-IN')}</div>
        <h3>Potential Annual Savings</h3>
      </motion.div>

      <motion.div className="result-card" variants={itemVariants}>
        <div className="result-card-header">
          <div className="result-icon">💰</div>
          <h2>Tax Computation Summary</h2>
        </div>
        <div className="result-content">
          <p><strong>Gross Income:</strong> ₹ {tax_analysis.gross_income.toLocaleString('en-IN')}</p>
          <p><strong>Total Deductions:</strong> ₹ {tax_analysis.total_deductions.toLocaleString('en-IN')}</p>
          <p><strong>Taxable Income:</strong> ₹ {tax_analysis.taxable_income.toLocaleString('en-IN')}</p>
          <hr style={{margin: '20px 0', border: '0', borderTop: '1px solid var(--gray-lighter)'}} />
          <p><strong>Tax (Old Regime):</strong> ₹ {tax_analysis.old_regime_tax.toLocaleString('en-IN')}</p>
          <p><strong>Tax (New Regime):</strong> ₹ {tax_analysis.new_regime_tax.toLocaleString('en-IN')}</p>
        </div>
      </motion.div>

      <motion.div className="result-card" variants={itemVariants}>
        <div className="result-card-header">
          <div className="result-icon">🔍</div>
          <h2>Risk Analysis</h2>
        </div>
        <div className="result-content">
          <p><strong>Audit Risk Score:</strong> {risk_analysis.audit_risk_score}/10 ({risk_analysis.risk_level})</p>
          {risk_analysis.flags.length > 0 && (
            <>
              <p><strong>Potential Red Flags:</strong></p>
              <ul>
                {risk_analysis.flags.map((flag, index) => <li key={index}>{flag}</li>)}
              </ul>
            </>
          )}
          <p><strong>Potential Penalty if Audited:</strong> ₹ {risk_analysis.penalty_if_audited.toLocaleString('en-IN')}</p>
        </div>
      </motion.div>

      <motion.div className="result-card" variants={itemVariants}>
        <div className="result-card-header">
          <div className="result-icon">💡</div>
          <h2>Strategy & Recommendations</h2>
        </div>
        <div className="result-content">
          <p><strong>Financial Health Score:</strong> {strategy_analysis.financial_health_score}/100</p>
          {strategy_analysis.missed_opportunities.length > 0 && (
            <>
              <p><strong>Missed Opportunities:</strong></p>
              <ul>
                {strategy_analysis.missed_opportunities.map((opp, index) => <li key={index}>{opp}</li>)}
              </ul>
            </>
          )}
          {strategy_analysis.recommended_actions.length > 0 && (
            <>
              <p><strong>Recommended Actions:</strong></p>
              <ul>
                {strategy_analysis.recommended_actions.map((action, index) => <li key={index}>{action}</li>)}
              </ul>
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default Results;
