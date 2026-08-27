import React from 'react';
import { motion } from 'framer-motion';
import './results.css';
import { CheckCircle2, Download, ChevronDown } from 'lucide-react';
import LoadingSkeleton from './LoadingSkeleton';

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
  if (!analysis) return <LoadingSkeleton lines={6} />;

  const {
    tax_analysis,
    risk_analysis,
    strategy_analysis
  } = analysis;
  const formatMoney = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  const downloadFilingPack = () => {
    const rows = (tax_analysis.filing_pack || []).map(row => `${row.item}\t${formatMoney(row.amount)}\t${row.itr_field}`);
    const content = ['TaxMate AI Filing Pack', '', 'Item\tAmount\tITR schedule / field', ...rows].join('\n');
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain' }));
    const link = document.createElement('a'); link.href = url; link.download = 'taxmate-filing-pack.txt'; link.click(); URL.revokeObjectURL(url);
  };
  const Breakdown = ({ regime, rows, rebate, marginalRelief, cess, total }) => <details className="calculation-details"><summary><ChevronDown size={17} /> How this was calculated - {regime} regime</summary><p className="agent-note">Tax Agent produced the regime math.</p>{(rows || []).map((row, index) => <div className="slab-row" key={`${regime}-${index}`}><span>{row.label}</span><strong>{formatMoney(row.tax)}</strong></div>)}<div className="slab-row"><span>Section 87A rebate</span><strong>-{formatMoney(rebate)}</strong></div>{marginalRelief > 0 && <div className="slab-row"><span>Marginal relief</span><strong>-{formatMoney(marginalRelief)}</strong></div>}<div className="slab-row"><span>Health and education cess: 4% of tax after relief</span><strong>{formatMoney(cess)}</strong></div><div className="slab-row"><span>Final tax including cess</span><strong>{formatMoney(total)}</strong></div></details>;

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
        <div className="results-actions"><button className="primary-action" onClick={downloadFilingPack}><Download size={17} /> Download Filing Pack</button><button className="secondary-action" onClick={() => window.print()}>Print / Save as PDF</button></div>
      </motion.div>

      <motion.div className="summary-card" variants={itemVariants}>
        <h3>Recommended Regime: <span style={{fontWeight: 800}}>{tax_analysis.recommended_regime.toUpperCase()}</span></h3>
        <div className="amount">₹ {Math.abs(tax_analysis.potential_savings).toLocaleString('en-IN')}</div>
        <h3>Potential Annual Savings</h3>
      </motion.div>
      {tax_analysis.legacy_calculation_warning && <motion.div className="legacy-warning" variants={itemVariants} role="alert"><strong>Pre-fix calculation notice</strong><p>This saved analysis was calculated before the tax rules were corrected. Its stored totals are preserved; run a new FY 2025-26 analysis to see corrected totals.</p></motion.div>}

      <motion.div className="agent-visibility" variants={itemVariants}>
        <div className="agent-visibility-heading"><div><p className="eyebrow">Analysis pipeline</p><h2>Three-agent review complete</h2></div><span>Dependency-ordered execution</span></div>
        <div className="agent-cards"><div><CheckCircle2 size={18} /><strong>Tax Agent</strong><span>Regime Analysis</span><em>Complete</em></div><div><CheckCircle2 size={18} /><strong>Risk Agent</strong><span>Audit Risk Scoring</span><em>Complete</em></div><div><CheckCircle2 size={18} /><strong>Strategy Agent</strong><span>Deduction Discovery</span><em>Complete</em></div></div>
      </motion.div>

      <motion.div className="result-card" variants={itemVariants}>
        <div className="result-card-header">
          <div className="result-icon">💰</div>
          <h2>Tax Computation Summary</h2>
        </div>
        <div className="result-content">
          <p><strong>Gross Income:</strong> ₹ {tax_analysis.gross_income.toLocaleString('en-IN')}</p>
          <p><strong>Total Deductions:</strong> ₹ {tax_analysis.total_deductions.toLocaleString('en-IN')}</p>
          <p><strong>Old Regime taxable income:</strong> ₹ {(tax_analysis.old_regime_taxable_income ?? tax_analysis.taxable_income).toLocaleString('en-IN')}</p>
          <p><strong>New Regime taxable income:</strong> ₹ {(tax_analysis.new_regime_taxable_income ?? tax_analysis.taxable_income).toLocaleString('en-IN')}</p>
          <hr style={{margin: '20px 0', border: '0', borderTop: '1px solid var(--gray-lighter)'}} />
          <p><strong>Tax (Old Regime):</strong> ₹ {tax_analysis.old_regime_tax.toLocaleString('en-IN')}</p>
          <p><strong>Tax (New Regime):</strong> ₹ {tax_analysis.new_regime_tax.toLocaleString('en-IN')}</p>
        </div>
      </motion.div>

      <motion.div className="result-card" variants={itemVariants}><div className="result-card-header"><div className="result-icon">🧾</div><h2>Filing Pack</h2><button className="text-action" onClick={downloadFilingPack}>Download table</button></div><p className="agent-note">Reference mapping for ITR-1/ITR-2. Verify against the current government form before filing.</p><div className="filing-table"><div className="filing-table-head"><span>Computed item</span><span>Amount</span><span>Portal schedule / field</span></div>{(tax_analysis.filing_pack || []).map(row => <div className="filing-table-row" key={row.item}><span>{row.item}</span><strong>{formatMoney(row.amount)}</strong><span>{row.itr_field}</span></div>)}</div></motion.div>

      <motion.div className="result-card" variants={itemVariants}><div className="result-card-header"><div className="result-icon">🧮</div><h2>Calculation transparency</h2></div><Breakdown regime="Old" rows={tax_analysis.old_regime_breakdown} rebate={tax_analysis.old_regime_rebate_87a} marginalRelief={tax_analysis.old_regime_marginal_relief} cess={tax_analysis.old_regime_cess} total={tax_analysis.old_regime_tax} /><Breakdown regime="New" rows={tax_analysis.new_regime_breakdown} rebate={tax_analysis.new_regime_rebate_87a} marginalRelief={tax_analysis.new_regime_marginal_relief} cess={tax_analysis.new_regime_cess} total={tax_analysis.new_regime_tax} /></motion.div>

      <motion.div className="regime-advisory" variants={itemVariants}><strong>Belated-return advisory</strong><p>Under Section 115BAC(6), a belated return filed after the original due date cannot choose the Old Regime. The taxpayer remains in the New Regime, regardless of which option would otherwise save more.</p></motion.div>

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
