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
import api from './services/api';

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
  const [currentStep, setCurrentStep] = useState('landing'); // landing, auth, verify, income, deductions, results, dashboard
  const [income, setIncome] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [userEmail, setUserEmail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await api.post('auth/refresh');
        const storedEmail = sessionStorage.getItem('user_email');
        if (storedEmail) {
          setUserEmail(storedEmail);
          setCurrentStep('income');
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
    setCurrentStep('income');
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

  const handleAnalyzeComplete = (analysisData) => {
    setAnalysis(analysisData);
    setCurrentStep('results');
  };

  const handleLogout = () => {
    sessionStorage.removeItem('user_email');
    setUserEmail(null);
    setCurrentStep('auth');
    setIncome(null);
    setAnalysis(null);
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
    return <LandingPage onGetStarted={handleGetStarted} />;
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'auth':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} />;
      case 'verify':
        return <Auth onUserCreated={handleUserCreated} onVerificationPending={handleVerificationPending} initialVerification />;
      case 'income':
        return <IncomeForm onIncomeSubmit={handleIncomeSubmitted} />;
      case 'deductions':
        return <DeductionForm incomeData={income} onAnalysisComplete={handleAnalyzeComplete} />;
      case 'results':
        return <Results analysis={analysis} />;
      case 'dashboard':
        return <ComplianceDashboard onBack={handleBackToResults} onNewAnalysis={handleNewAnalysis} />;
      default:
        return <LandingPage onGetStarted={handleGetStarted} />;
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            TAXMATE AI
          </div>
          <div className="user-info">
            {userEmail && <span className="user-email">{userEmail}</span>}
            {userEmail && currentStep !== 'dashboard' && (
              <button onClick={handleOpenDashboard} className="dashboard-btn">Compliance Dashboard</button>
            )}
            {currentStep === 'dashboard' && (
              <button onClick={handleBackToResults} className="new-analysis-btn">Back</button>
            )}
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        </div>
      </header>
      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial="initial"
            animate="in"
            exit="out"
            variants={pageVariants}
            transition={pageTransition}
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Chat Widget - Available everywhere */}
      <AnimatePresence>
        {chatOpen && (
          <Chat 
            analysis={analysis || {}} 
            onClose={() => setChatOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Floating Chat Button - Visible everywhere */}
      {!chatOpen && currentStep !== 'landing' && (
        <motion.button
          className="floating-chat-btn"
          onClick={() => setChatOpen(true)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          title="Open AI Tax Assistant"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
        >
          💬
        </motion.button>
      )}
    </div>
  );
}

export default App;
