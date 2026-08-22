import React from 'react';
import { motion } from 'framer-motion';
import '../styles/LandingPage.css';

const cardVariants = {
  hidden: { opacity: 0, y: 50 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: 'easeOut',
    },
  }),
};

function LandingPage({ onGetStarted }) {
  return (
    <motion.div 
      className="landing-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Navigation */}
      <motion.nav 
        className="landing-nav"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className="nav-content">
          <div className="nav-logo">
            <span className="nav-title">TAXMATE AI</span>
          </div>
          <button className="nav-cta" onClick={onGetStarted}>
            Get Started
          </button>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <motion.div 
            className="hero-text"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
          >
            <h1 className="hero-title">
              Intelligent Tax Planning, <span>Simplified.</span>
            </h1>
            <p className="hero-subtitle">
              Leverage the power of AI to uncover hidden tax savings, optimize your financial strategy, and file with confidence.
            </p>
            <motion.button 
              className="hero-cta" 
              onClick={onGetStarted}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Start Your Free Analysis
              <span className="arrow">→</span>
            </motion.button>
          </motion.div>
          <div className="hero-visual">
            <motion.div 
              className="hero-graphic"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.4 }}
            >
              <motion.div className="graphic-card card-1" animate={{ y: [0, -10, 0] }} transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}>📊</motion.div>
              <motion.div className="graphic-card card-2" animate={{ y: [0, 15, 0] }} transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}>💰</motion.div>
              <motion.div className="graphic-card card-3" animate={{ y: [0, -12, 0] }} transition={{ repeat: Infinity, duration: 3.5, ease: "easeInOut" }}>🎯</motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="features-header">
          <h2>Why Choose TAXMATE AI?</h2>
          <p>Unlock a smarter way to manage your taxes.</p>
        </div>
        <div className="features-grid">
          {[
            { icon: '🤖', title: 'AI-Powered Analysis', text: 'Our advanced AI analyzes your finances to find every possible deduction and credit.' },
            { icon: '⚡', title: 'Fast & Intuitive', text: 'A streamlined process guides you through your tax analysis in minutes, not hours.' },
            { icon: '🔒', title: 'Bank-Level Security', text: 'Your data is protected with end-to-end encryption and strict privacy protocols.' },
            { icon: '💡', title: 'Personalized Strategies', text: 'Receive actionable advice tailored to your unique financial situation and goals.' },
            { icon: '📈', title: 'Maximize Your Refund', text: 'Identify opportunities to legally minimize your tax liability and boost your returns.' },
            { icon: '📋', title: 'Comprehensive Reports', text: 'Get detailed, easy-to-understand reports that break down your tax situation.' },
          ].map((feature, i) => (
            <motion.div 
              className="feature-card" 
              key={i}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.5 }}
              variants={cardVariants}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2>Simple Steps to Tax Clarity</h2>
        <div className="steps-wrapper">
          {[
            { number: 1, title: 'Secure Sign-Up', text: 'Create your account in seconds with just your email.' },
            { number: 2, title: 'Input Your Data', text: 'Easily enter your income and deduction information.' },
            { number: 3, title: 'Run AI Analysis', text: 'Our AI gets to work, analyzing your data for optimizations.' },
            { number: 4, title: 'Get Your Results', text: 'Receive your personalized tax strategy and insights.' },
          ].map((step, i) => (
             <motion.div 
              className="process-step" 
              key={i}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.5 }}
              variants={cardVariants}
            >
              <div className="step-number">{step.number}</div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-logo">TAXMATE AI</div>
          <div className="footer-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#privacy">Privacy Policy</a>
          </div>
          <p className="footer-copyright">
            © {new Date().getFullYear()} TAXMATE AI. All Rights Reserved.
          </p>
        </div>
      </footer>
    </motion.div>
  );
}

export default LandingPage;
