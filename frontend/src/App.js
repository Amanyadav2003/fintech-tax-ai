import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import './components/navigation.css';
import LandingPage from './components/LandingPage';
import Auth from './components/Auth';
import IncomeForm from './components/IncomeForm';
import IncomeTypeSelection from './components/IncomeTypeSelection';
import DeductionForm from './components/DeductionForm';
import Results from './components/Results';
import ComplianceDashboard from './components/ComplianceDashboard';
import Chat from './components/Chat';
import Profile from './components/Profile';
import ProfileMenu from './components/ProfileMenu';
import Home from './components/Home';
import History from './components/History';
import ExpenseTracker from './components/ExpenseTracker';
import Documents from './components/Documents';
import Changelog from './components/Changelog';
import ResourceRoute, { ResourcesMenu } from './components/Resources';
import api from './services/api';
import AppBackground from './components/AppBackground';
import { AlertTriangle, MessageCircle, X } from 'lucide-react';
import { isUpdateUnread, UPDATE_READ_EVENT } from './data/updates';

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

const protectedSteps = ['home', 'income-type', 'income', 'deductions', 'results', 'history', 'expenses', 'dashboard', 'profile', 'documents'];

function App() {
  const [currentStep, setCurrentStep] = useState('landing'); // landing, auth, verify, home, income-type, income, deductions, results, history
  const [income, setIncome] = useState(null);
  const [incomeType, setIncomeType] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [userEmail, setUserEmail] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [documentValues, setDocumentValues] = useState({});
  const [documentReviewSeed, setDocumentReviewSeed] = useState(null);
  const [sessionNotice, setSessionNotice] = useState('');
  const [hasUnreadUpdate, setHasUnreadUpdate] = useState(() => isUpdateUnread());
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('taxmate-theme');
    return saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('taxmate-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  useEffect(() => {
    const decodeExpiry = () => {
      try {
        const token = sessionStorage.getItem('access_token');
        if (!token) return null;
        const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
        return payload.exp ? payload.exp * 1000 : null;
      } catch { return null; }
    };

    let warningTimer;
    let expiryTimer;
    let refreshInFlight = false;
    let lastActivityRefresh = 0;
    const schedule = () => {
      window.clearTimeout(warningTimer);
      window.clearTimeout(expiryTimer);
      const expiresAt = decodeExpiry();
      if (!expiresAt) return;
      const warningDelay = Math.max(0, expiresAt - Date.now() - 120000);
      const expiryDelay = Math.max(0, expiresAt - Date.now());
      warningTimer = window.setTimeout(() => setSessionNotice('warning'), warningDelay);
      expiryTimer = window.setTimeout(() => setSessionNotice('expired'), expiryDelay);
    };
    const refreshOnActivity = () => {
      if (!userEmail || refreshInFlight || Date.now() - lastActivityRefresh < 30000) return;
      lastActivityRefresh = Date.now();
      refreshInFlight = true;
      api.post('auth/refresh').then(() => { setSessionNotice(''); schedule(); }).catch(() => {}).finally(() => { refreshInFlight = false; });
    };
    const handleExpiry = () => setSessionNotice('expired');
    const activityEvents = ['click', 'keydown', 'touchstart'];
    activityEvents.forEach(event => window.addEventListener(event, refreshOnActivity));
    window.addEventListener('taxmate:session-expired', handleExpiry);
    schedule();
    return () => {
      activityEvents.forEach(event => window.removeEventListener(event, refreshOnActivity));
      window.removeEventListener('taxmate:session-expired', handleExpiry);
      window.clearTimeout(warningTimer);
      window.clearTimeout(expiryTimer);
    };
  }, [userEmail]);

  useEffect(() => {
    const refreshUpdateBadge = () => setHasUnreadUpdate(isUpdateUnread());
    window.addEventListener(UPDATE_READ_EVENT, refreshUpdateBadge);
    window.addEventListener('storage', refreshUpdateBadge);
    return () => {
      window.removeEventListener(UPDATE_READ_EVENT, refreshUpdateBadge);
      window.removeEventListener('storage', refreshUpdateBadge);
    };
  }, []);

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

  useEffect(() => {
    if (!userEmail && protectedSteps.includes(currentStep)) setCurrentStep('auth');
  }, [currentStep, userEmail]);

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

  const handleIncomeTypeSelected = (selectedType) => {
    setIncomeType(selectedType);
    setCurrentStep('income');
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
        old_regime_breakdown: taxOutput.tax_old_regime?.slab_breakdown || [],
        new_regime_breakdown: taxOutput.tax_new_regime?.slab_breakdown || [],
        old_regime_rebate_87a: taxOutput.tax_old_regime?.rebate_87a || 0,
        new_regime_rebate_87a: taxOutput.tax_new_regime?.rebate_87a || 0,
        old_regime_marginal_relief: taxOutput.tax_old_regime?.marginal_relief || 0,
        new_regime_marginal_relief: taxOutput.tax_new_regime?.marginal_relief || 0,
        old_regime_cess: taxOutput.tax_old_regime?.health_education_cess || 0,
        new_regime_cess: taxOutput.tax_new_regime?.health_education_cess || 0,
        filing_pack: [],
        legacy_calculation_warning: result.legacy_calculation_warning,
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
    setIncomeType(null);
    setCurrentStep('income-type');
  };

  const handleApplyDocumentValues = (values) => {
    setDocumentValues(values);
    const deductionKeys = ['investments_80c', 'health_insurance_80d', 'home_loan_interest_24b', 'rent_paid_80gg', 'donations_80g', 'other_deductions'];
    setCurrentStep(Object.keys(values).some(key => deductionKeys.includes(key)) ? 'deductions' : 'income');
  };

  const handleOpenDashboard = () => {
    setCurrentStep('dashboard');
  };

  const handleOpenDocuments = (seed = null) => {
    setDocumentReviewSeed(seed);
    setCurrentStep('documents');
  };

  const handleBackToResults = () => {
    setCurrentStep(analysis ? 'results' : 'income-type');
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
        {userEmail && <ChatWidget chatOpen={chatOpen} setChatOpen={setChatOpen} analysis={analysis} />}
      </AppBackground>
    );
  }

  const stayLoggedIn = () => {
    setSessionNotice('');
    api.post('auth/refresh').then(() => window.dispatchEvent(new Event('taxmate:session-refreshed'))).catch(() => setSessionNotice('expired'));
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'auth':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} />;
      case 'verify':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} initialVerification />;
      case 'income-type':
        return <IncomeTypeSelection onSelect={handleIncomeTypeSelected} />;
      case 'income':
        return <IncomeForm incomeType={incomeType} onIncomeSubmit={handleIncomeSubmitted} userEmail={userEmail} documentValues={documentValues} />;
      case 'deductions':
        return <DeductionForm incomeData={income} onAnalysisComplete={handleAnalyzeComplete} userEmail={userEmail} documentValues={documentValues} />;
      case 'results':
        return <Results analysis={analysis} />;
      case 'home':
        return <Home user={user || { email: userEmail }} onStart={() => setCurrentStep('income-type')} onHistory={() => setCurrentStep('history')} onViewResult={handleViewResult} onOpenDocuments={handleOpenDocuments} />;
      case 'history':
        return <History onBack={() => setCurrentStep('home')} onViewResult={handleViewResult} />;
      case 'expenses':
        return <ExpenseTracker onBack={() => setCurrentStep('home')} />;
      case 'dashboard':
        return <ComplianceDashboard onBack={handleBackToResults} onNewAnalysis={handleNewAnalysis} />;
      case 'profile':
        return <Profile user={user || { email: userEmail }} />;
      case 'documents':
        return <Documents onApplyValues={handleApplyDocumentValues} reviewSeed={documentReviewSeed} />;
      case 'changelog':
        return <Changelog onBack={() => setCurrentStep(userEmail ? 'home' : 'auth')} />;
      case 'resource-income-tax':
      case 'resource-hra':
      case 'resource-advance-tax':
      case 'guide-regime':
      case 'guide-documents':
      case 'guide-deductions':
      case 'guide-risk':
        return <ResourceRoute step={currentStep} />;
      default:
        return <LandingPage onGetStarted={handleGetStarted} />;
    }
  };

  const pageNames = { 'income-type': 'Choose your income type', income: 'Income Sources', deductions: 'Deductions', results: 'Results', history: 'History', expenses: 'Expense Tracker', profile: 'Profile', dashboard: 'Compliance Dashboard', documents: 'My Documents', changelog: "What's New", home: 'Home', 'resource-income-tax': 'Income Tax Calculator', 'resource-hra': 'HRA Exemption Calculator', 'resource-advance-tax': 'Advance Tax Calculator' };
  const currentPageName = pageNames[currentStep] || (currentStep.startsWith('guide-') ? 'Guide' : 'Workspace');

  return (
    <AppBackground variant="subtle">
      <div className="App">
      {sessionNotice && <div className={`session-toast ${sessionNotice}`} role="alert"><AlertTriangle size={18} /><span>{sessionNotice === 'warning' ? 'Your session will expire soon due to inactivity — click anywhere to stay logged in.' : 'Your session expired, please log in again.'}</span>{sessionNotice === 'warning' ? <button className="session-toast-close" onClick={stayLoggedIn} aria-label="Stay logged in">Stay logged in</button> : <button className="session-toast-close" onClick={() => { setSessionNotice(''); setCurrentStep('auth'); }} aria-label="Dismiss session expired message"><X size={17} /></button>}</div>}
      <header className="app-header">
        <div className="header-content">
          <button className="logo" onClick={() => userEmail && setCurrentStep('home')} aria-label="Go to Home">
            TAXMATE AI
          </button>
          <nav className="top-nav" aria-label="Primary navigation"><button onClick={() => setCurrentStep('home')}>Home</button><ResourcesMenu onNavigate={setCurrentStep} hasUnreadUpdate={hasUnreadUpdate} /><span>{currentPageName}</span></nav>
          <div className="user-info">
            {userEmail && user && <ProfileMenu user={user} onProfile={() => setCurrentStep('profile')} onDashboard={handleOpenDashboard} onHistory={() => setCurrentStep('history')} onExpenses={() => setCurrentStep('expenses')} onDocuments={() => setCurrentStep('documents')} onLogout={handleLogout} darkMode={darkMode} onToggleDarkMode={() => setDarkMode(previous => !previous)} />}
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

      {userEmail && <ChatWidget chatOpen={chatOpen} setChatOpen={setChatOpen} analysis={analysis} />}
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
