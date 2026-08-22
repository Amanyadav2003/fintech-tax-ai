import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import LandingPage from './components/LandingPage';
import Auth from './components/Auth';
import IncomeForm from './components/IncomeForm';
import DeductionForm from './components/DeductionForm';
import Results from './components/Results';
import ComplianceDashboard from './components/ComplianceDashboard';
import Chat from './components/Chat';
import Profile from './components/Profile';
import ProfileMenu from './components/ProfileMenu';
import Home from './components/Home';
import History from './components/History';
import ExpenseTracker from './components/ExpenseTracker';
import api from './services/api';
import AppBackground from './components/AppBackground';
import { MessageCircle } from 'lucide-react';

const pageVariants = {
  initial: {
    opacity: 0,
    y: 30
  },
  in: {
    opacity: 1,
    y: 0
  },
  out: {
    opacity: 0,
    y: -30
  }
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.5
};

function App() {
  const [currentStep, setCurrentStep] = useState('landing'); // landing, auth, verify, home, income, deductions, results, history
  const [income, setIncome] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [userEmail, setUserEmail] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await api.post('auth/refresh');
        const profileResponse = await api.get('auth/me');
        const profile = profileResponse.data;
        if (profile.email) {
          setUser(profile);
          setUserEmail(profile.email);
          setCurrentStep('home');
        } else {
          setCurrentStep('landing');
        }
      } catch (err) {
        setCurrentStep('landing');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const handleGetStarted = () => {
    setCurrentStep('auth');
  };

  const handleUserCreated = (email) => {
    setUserEmail(email);
    sessionStorage.setItem('user_email', email);
    setCurrentStep('home');
    api.get('auth/me').then(response => setUser(response.data)).catch(() => {});
  };

  const handleVerificationPending = (email) => {
    setUserEmail(null);
    setCurrentStep('verify');
    sessionStorage.setItem('pending_verification_email', email);
  };

  const handleIncomeSubmitted = (incomeData) => {
    setIncome(incomeData);
    setCurrentStep('deductions');
  };

  const handleViewResult = async (filingId) => {
    const response = await api.get(`tax/results/${filingId}`);
    const result = response.data;
    const taxOutput = result.tax_agent_output || {};
    const riskOutput = result.risk_agent_output || {};
    const strategyOutput = result.strategy_agent_output || {};
    setAnalysis({
      tax_analysis: {
        recommended_regime: result.recommended_regime,
        potential_savings: Math.abs(result.tax_old_regime - result.tax_new_regime),
        gross_income: result.total_income,
        total_deductions: result.total_deductions,
        taxable_income: taxOutput.tax_old_regime?.taxable_income || 0,
        old_regime_tax: result.tax_old_regime,
        new_regime_tax: result.tax_new_regime,
      },
      risk_analysis: { audit_risk_score: riskOutput.overall_audit_risk_score || 0, risk_level: riskOutput.risk_level || 'GREEN', flags: (riskOutput.audit_flags || []).map(flag => flag.reason), penalty_if_audited: 0 },
      strategy_analysis: { financial_health_score: strategyOutput.financial_health_score || 0, missed_opportunities: [], recommended_actions: (strategyOutput.next_actions || []).map(action => action.action || action) },
    });
    setCurrentStep('results');
  };

  const handleAnalyzeComplete = (analysisData) => {
    setAnalysis(analysisData);
    setCurrentStep('results');
  };

  const handleLogout = async () => {
    try { await api.post('auth/logout'); } catch (err) { /* local sign-out still clears the session */ }
    sessionStorage.removeItem('user_email');
    setUserEmail(null);
    setCurrentStep('auth');
    setIncome(null);
    setAnalysis(null);
    setUser(null);
  };

  const handleNewAnalysis = () => {
    setIncome(null);
    setAnalysis(null);
    setCurrentStep('income');
  };

  const handleOpenDashboard = () => {
    setCurrentStep('dashboard');
  };

  const handleBackToResults = () => {
    setCurrentStep(analysis ? 'results' : 'income');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading Intelligent Engine...</p>
      </div>
    );
  }

  if (currentStep === 'landing') {
    return (
      <AppBackground variant="vibrant">
        <LandingPage onGetStarted={handleGetStarted} />
        <ChatWidget chatOpen={chatOpen} setChatOpen={setChatOpen} analysis={analysis} />
      </AppBackground>
    );
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'auth':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} />;
      case 'verify':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} initialVerification />;
      case 'income':
        return <IncomeForm onIncomeSubmit={handleIncomeSubmitted} userEmail={userEmail} />;
      case 'deductions':
        return <DeductionForm incomeData={income} onAnalysisComplete={handleAnalyzeComplete} userEmail={userEmail} />;
      case 'results':
        return <Results analysis={analysis} />;
      case 'home':
        return <Home user={user || { email: userEmail }} onStart={() => setCurrentStep('income')} onHistory={() => setCurrentStep('history')} onViewResult={handleViewResult} />;
      case 'history':
        return <History onBack={() => setCurrentStep('home')} onViewResult={handleViewResult} />;
      case 'expenses':
        return <ExpenseTracker onBack={() => setCurrentStep('home')} />;
      case 'dashboard':
        return <ComplianceDashboard onBack={handleBackToResults} onNewAnalysis={handleNewAnalysis} />;
      case 'profile':
        return <Profile user={user || { email: userEmail }} />;
      default:
        return <LandingPage onGetStarted={handleGetStarted} />;
    }
  };

  return (
    <AppBackground variant="subtle">
      <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            TAXMATE AI
          </div>
          <div className="user-info">
            {userEmail && user && <ProfileMenu user={user} onProfile={() => setCurrentStep('profile')} onDashboard={handleOpenDashboard} onHistory={() => setCurrentStep('history')} onExpenses={() => setCurrentStep('expenses')} onLogout={handleLogout} />}
            {currentStep === 'dashboard' && (
              <button onClick={handleBackToResults} className="new-analysis-btn">Back</button>
            )}
          </div>
        </div>
      </header>
      <main className="main-content">
        <motion.div
          key={currentStep}
          initial="initial"
          animate="in"
          variants={pageVariants}
          transition={pageTransition}
        >
          {renderStep()}
        </motion.div>
      </main>

      <ChatWidget chatOpen={chatOpen} setChatOpen={setChatOpen} analysis={analysis} />
      </div>
    </AppBackground>
  );
}

function ChatWidget({ chatOpen, setChatOpen, analysis }) {
  return (
    <div className="chat-widget-layer">
      <AnimatePresence>
        {chatOpen && <Chat analysis={analysis || {}} onClose={() => setChatOpen(false)} />}
      </AnimatePresence>
      {!chatOpen && (
        <motion.button
          className="floating-chat-btn"
          onClick={() => setChatOpen(true)}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.94 }}
          title="Open AI Tax Assistant"
          aria-label="Open AI Tax Assistant"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <MessageCircle size={25} strokeWidth={2.2} />
        </motion.button>
      )}
    </div>
  );
}

export default App;
