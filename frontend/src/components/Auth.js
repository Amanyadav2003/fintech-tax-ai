import React, { useState } from 'react';
import { motion } from 'framer-motion';
import './auth.css';
import api from '../services/api';

const formVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0 }
};

function Auth({ onUserCreated, onVerificationPending, initialVerification = false }) {
  const [isLogin, setIsLogin] = useState(true);
  const [isVerifying, setIsVerifying] = useState(initialVerification);
  const [otp, setOtp] = useState('');
  const [resendCountdown, setResendCountdown] = useState(0);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    pan: '',
    age: '',
    state: 'Maharashtra',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  React.useEffect(() => {
    const pendingEmail = sessionStorage.getItem('pending_verification_email');
    if (initialVerification && pendingEmail) {
      setFormData(prev => ({ ...prev, email: pendingEmail }));
      setIsVerifying(true);
      setResendCountdown(60);
    }
  }, [initialVerification]);

  React.useEffect(() => {
    if (!resendCountdown) return undefined;
    const timer = window.setInterval(() => setResendCountdown(value => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [resendCountdown]);

  // Real-time field validation
  const validateField = (name, value) => {
    let error = '';

    if (!value.trim()) {
      return ''; // Don't show error for empty field yet
    }

    switch (name) {
      case 'name':
        if (value.trim().length < 2) {
          error = 'Must be at least 2 characters long.';
        } else if (value.trim().length > 100) {
          error = 'Name must be less than 100 characters.';
        }
        break;

      case 'email':
        if (!value.includes('@')) {
          error = "Please include an '@' in the email address.";
        } else if (value.length < 5) {
          error = 'Email is too short.';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          error = 'Please enter a valid email address.';
        }
        break;

      case 'phone':
        if (value.length < 10) {
          error = 'Phone number must be exactly 10 digits.';
        } else if (value.length > 10) {
          error = 'Phone number must be exactly 10 digits.';
        } else if (!/^\d{10}$/.test(value)) {
          error = 'Phone number must contain only digits.';
        }
        break;

      case 'pan':
        if (value.length < 10) {
          error = 'PAN must be 10 characters.';
        } else if (value.length > 10) {
          error = 'PAN must be 10 characters.';
        } else if (!/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(value.toUpperCase())) {
          error = 'Invalid format. Must be like ABCDE1234F (5 letters, 4 numbers, 1 letter).';
        }
        break;

      case 'age':
        if (value && parseInt(value) < 18) {
          error = 'You must be at least 18 years old.';
        } else if (value && parseInt(value) > 100) {
          error = 'Age must be 100 or less.';
        }
        break;

      case 'password':
        if (value.length < 8) {
          error = 'Password must be at least 8 characters long.';
        } else if (!/[A-Z]/.test(value)) {
          error = 'Password must include at least one uppercase letter.';
        } else if (!/[0-9]/.test(value)) {
          error = 'Password must include at least one number.';
        } else if (!/[!@#$%^&*]/.test(value)) {
          error = 'Password must include at least one special character (!@#$%^&*).';
        }
        break;

      default:
        break;
    }

    // Update field errors state
    setFieldErrors(prev => {
      if (error) {
        return { ...prev, [name]: error };
      } else {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      }
    });

    return error;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
    
    // Real-time validation
    if (value.trim()) {
      validateField(name, value);
    } else {
      // Clear field error if empty
      setFieldErrors(prev => {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      });
    }
  };

  const getFieldSpecificMessage = (field, msg) => {
    // Create readable field labels
    const fieldLabels = {
      'name': 'Full Name',
      'email': 'Email Address',
      'password': 'Password',
      'phone': 'Phone Number',
      'pan': 'PAN Card',
      'age': 'Age',
      'state': 'State'
    };
    
    const fieldLabel = fieldLabels[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const icon = {
      'name': '👤',
      'email': '📧',
      'password': '🔐',
      'phone': '📱',
      'pan': '📋',
      'age': '🎂',
      'state': '🗺️'
    }[field] || '⚠️';

    const msgLower = msg.toLowerCase();

    // Email-specific messages
    if (field === 'email') {
      if (msgLower.includes('@-sign') || msgLower.includes('valid email')) {
        return `${icon} ${fieldLabel}: Please include an '@' in the email address.`;
      }
      if (msgLower.includes('too short') || msgLower.includes('at least')) {
        return `${icon} ${fieldLabel}: Email is too short.`;
      }
    }

    // Name-specific messages
    if (field === 'name') {
      if (msgLower.includes('too short') || msgLower.includes('at least 2')) {
        return `${icon} ${fieldLabel}: Must be at least 2 characters long.`;
      }
      if (msgLower.includes('too long') || msgLower.includes('at most')) {
        return `${icon} ${fieldLabel}: Name must be less than 100 characters.`;
      }
    }

    // Phone-specific messages
    if (field === 'phone') {
      if (msgLower.includes('pattern') || msgLower.includes('match')) {
        return `${icon} ${fieldLabel}: Phone number must be exactly 10 digits (e.g., 9876543210).`;
      }
      if (msgLower.includes('too short') || msgLower.includes('at least')) {
        return `${icon} ${fieldLabel}: Phone number must be 10 digits.`;
      }
    }

    // PAN-specific messages
    if (field === 'pan') {
      if (msgLower.includes('pattern') || msgLower.includes('match')) {
        return `${icon} ${fieldLabel}: Must be 10 characters in format ABCDE1234F (5 letters, 4 numbers, 1 letter).`;
      }
      if (msgLower.includes('too short') || msgLower.includes('at least')) {
        return `${icon} ${fieldLabel}: PAN must be 10 characters.`;
      }
    }

    // Age-specific messages
    if (field === 'age') {
      if (msgLower.includes('greater than') || msgLower.includes('18') || msgLower.includes('ge')) {
        return `${icon} ${fieldLabel}: You must be at least 18 years old.`;
      }
      if (msgLower.includes('at most') || msgLower.includes('le')) {
        return `${icon} ${fieldLabel}: Age must be 100 or less.`;
      }
    }

    // Password-specific messages
    if (field === 'password') {
      if (msgLower.includes('at least 8') || msgLower.includes('8 characters')) {
        return `${icon} ${fieldLabel}: Password must be at least 8 characters long.`;
      }
      if (msgLower.includes('uppercase')) {
        return `${icon} ${fieldLabel}: Password must include at least one uppercase letter.`;
      }
      if (msgLower.includes('digit')) {
        return `${icon} ${fieldLabel}: Password must include at least one number.`;
      }
      if (msgLower.includes('special character')) {
        return `${icon} ${fieldLabel}: Password must include at least one special character (!@#$%^&*).`;
      }
    }

    // Default fallback with pattern matching
    if (msgLower.includes('too short') || msgLower.includes('at least')) {
      return `${icon} ${fieldLabel}: This field is too short.`;
    }
    if (msgLower.includes('too long') || msgLower.includes('at most')) {
      return `${icon} ${fieldLabel}: This field is too long.`;
    }
    if (msgLower.includes('pattern') || msgLower.includes('match')) {
      return `${icon} ${fieldLabel}: Invalid format for this field.`;
    }
    if (msgLower.includes('greater than') || msgLower.includes('must be')) {
      return `${icon} ${fieldLabel}: Value does not meet minimum requirements.`;
    }

    return `${icon} ${fieldLabel}: ${msg}`;
  };

  const getDetailedErrorMessage = (err) => {
    // Connection/Network errors
    if (!err.response) {
      if (err.code === 'ECONNABORTED') {
        return '⏱️ Request timed out. Please check your internet connection and try again.';
      }
      if (err.message === 'Network Error') {
        return '🔌 Connection failed. Backend server might not be running. Please try again later.';
      }
      return `❌ Network error: ${err.message}`;
    }

    const status = err.response.status;
    const data = err.response.data;

    // Server-side validation errors (422)
    if (status === 422) {
      // Check for detailed errors field first
      if (data.errors && Array.isArray(data.errors)) {
        const fieldErrors = data.errors.map(error => {
          const field = error.loc && error.loc.length > 0 ? error.loc[error.loc.length - 1] : 'Field';
          const msg = error.msg || 'Invalid';
          
          // Generate specific error messages based on field and error type
          const specificMessage = getFieldSpecificMessage(field, msg);
          return specificMessage;
        }).join('\n');
        return fieldErrors || '❌ Validation error. Please check your input.';
      } else if (Array.isArray(data.detail)) {
        const fieldErrors = data.detail.map(error => {
          const field = error.loc && error.loc.length > 0 ? error.loc[error.loc.length - 1] : 'Field';
          const msg = error.msg || 'Invalid';
          
          const specificMessage = getFieldSpecificMessage(field, msg);
          return specificMessage;
        }).join('\n');
        return fieldErrors || '❌ Validation error. Please check your input.';
      } else if (typeof data.detail === 'string') {
        return `⚠️ ${data.detail}`;
      } else {
        return '❌ Validation error. Please check your input.';
      }
    }

    // Login/Auth specific errors (401)
    if (status === 401) {
      if (data.detail === 'Invalid credentials') {
        return '🔐 Invalid email or password. Please check and try again.';
      }
      if (data.detail === 'User account is disabled') {
        return '⛔ Your account has been disabled. Please contact support.';
      }
      if (data.detail === 'No access token provided') {
        return '⛔ Authentication failed. Please log in again.';
      }
      return `⛔ Authentication failed: ${data.detail || 'Unknown error'}`;
    }

    if (status === 403 || status === 429) {
      return `${status === 429 ? '⏳' : '⛔'} ${data.detail || 'Request blocked'}`;
    }

    // Already registered errors (400)
    if (status === 400) {
      if (data.detail && data.detail.includes('already registered')) {
        return '📧 This email or PAN is already registered. Try logging in instead.';
      }
      if (data.detail && data.detail.includes('Invalid PAN')) {
        return '❌ Invalid PAN format. Must be 10 characters (example: ABCDE1234F)';
      }
      return `⚠️ ${data.detail || 'Invalid request'}`;
    }

    // Server errors (500+)
    if (status >= 500) {
      return '🔧 Server error. Please try again later.';
    }

    // Generic error handling
    if (data.detail) {
      if (typeof data.detail === 'string') {
        return `⚠️ ${data.detail}`;
      }
      if (typeof data.detail === 'object') {
        return `⚠️ ${JSON.stringify(data.detail)}`;
      }
    }

    return `❌ Error (${status}): Something went wrong. Please try again.`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isVerifying) {
        const response = await api.post('auth/verify-otp', { email: formData.email, otp });
        sessionStorage.removeItem('pending_verification_email');
        sessionStorage.setItem('access_token', response.data.access_token);
        sessionStorage.setItem('user_email', formData.email);
        onUserCreated(formData.email);
        return;
      }

      const endpoint = isLogin ? 'auth/login' : 'auth/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : {
            email: formData.email,
            password: formData.password,
            name: formData.name,
            phone: formData.phone,
            pan: formData.pan.toUpperCase(),
            age: parseInt(formData.age),
            state: formData.state,
          };

      const response = await api.post(endpoint, payload);
      
      // Store token if login was successful
      if (isLogin && response.data.access_token) {
        sessionStorage.setItem('access_token', response.data.access_token);
        sessionStorage.setItem('user_email', formData.email);
        onUserCreated(formData.email);
      } else if (!isLogin) {
        setIsVerifying(true);
        setIsLogin(false);
        setOtp('');
        setResendCountdown(60);
        sessionStorage.setItem('pending_verification_email', formData.email);
        onVerificationPending(formData.email);
      }

    } catch (err) {
      console.error('Auth error:', err);
      const errorMessage = getDetailedErrorMessage(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendCountdown || loading) return;
    setLoading(true);
    setError('');
    try {
      await api.post('auth/resend-otp', { email: formData.email });
      setResendCountdown(60);
    } catch (err) {
      setError(getDetailedErrorMessage(err));
      if (err.response?.status === 429) setResendCountdown(60);
    } finally {
      setLoading(false);
    }
  };

  if (isVerifying) {
    return (
      <div className="auth-container">
        <motion.div className="auth-card" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
          <h1>Verify Your Email</h1>
          <p>Enter the 6-digit code sent to {formData.email}.</p>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <input className="otp-input" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength="6" pattern="\d{6}" placeholder="000000" value={otp} onChange={(e) => { setOtp(e.target.value.replace(/\D/g, '')); setError(''); }} required aria-label="6-digit verification code" />
            </div>
            <button className="auth-btn" type="submit" disabled={loading || otp.length !== 6}>
              {loading ? <div className="spinner" /> : 'Verify Email'}
            </button>
          </form>
          <button className="resend-btn" type="button" onClick={handleResend} disabled={loading || resendCountdown > 0}>
            {resendCountdown > 0 ? `Resend OTP in ${resendCountdown}s` : 'Resend OTP'}
          </button>
          <p className="toggle-auth"><span onClick={() => { setIsVerifying(false); setIsLogin(true); setError(''); }}>Use a different account</span></p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <motion.div 
        className="auth-card"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <h1>{isLogin ? 'Welcome Back' : 'Create Your Account'}</h1>
        <p>{isLogin ? 'Log in to access your AI tax assistant.' : 'Join to unlock intelligent tax insights.'}</p>
        
        {error && <div className="error-message">{error}</div>}

        <motion.form onSubmit={handleSubmit} variants={formVariants} initial="hidden" animate="visible">
          {!isLogin && (
            <>
              <motion.div variants={itemVariants} className="form-group">
                <input type="text" name="name" placeholder="Full Name" value={formData.name} onChange={handleChange} required className={fieldErrors.name ? 'input-error' : ''} />
                {fieldErrors.name && <div className="field-error-message">👤 {fieldErrors.name}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <input type="text" name="pan" placeholder="PAN Card" value={formData.pan} onChange={handleChange} required maxLength="10" className={fieldErrors.pan ? 'input-error' : ''} />
                {fieldErrors.pan && <div className="field-error-message">📋 {fieldErrors.pan}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <input type="tel" name="phone" placeholder="Phone Number" value={formData.phone} onChange={handleChange} required className={fieldErrors.phone ? 'input-error' : ''} />
                {fieldErrors.phone && <div className="field-error-message">📱 {fieldErrors.phone}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <input type="number" name="age" placeholder="Age" value={formData.age} onChange={handleChange} required className={fieldErrors.age ? 'input-error' : ''} />
                {fieldErrors.age && <div className="field-error-message">🎂 {fieldErrors.age}</div>}
              </motion.div>
            </>
          )}

          <motion.div variants={itemVariants} className="form-group">
            <input type="email" name="email" placeholder="Email Address" value={formData.email} onChange={handleChange} required className={fieldErrors.email ? 'input-error' : ''} />
            {fieldErrors.email && <div className="field-error-message">📧 {fieldErrors.email}</div>}
          </motion.div>

          <motion.div variants={itemVariants} className="form-group">
            <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required className={fieldErrors.password ? 'input-error' : ''} />
            {fieldErrors.password && <div className="field-error-message">🔐 {fieldErrors.password}</div>}
          </motion.div>
          
          {!isLogin && (
            <motion.div variants={itemVariants} style={{ fontSize: '12px', color: '#666', marginTop: '-10px', marginBottom: '10px' }}>
              Password must include: uppercase letter, number, and special character (!@#$%^&*)
            </motion.div>
          )}
          
          <motion.button 
            className="auth-btn" 
            type="submit" 
            disabled={loading}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? <div className="spinner" /> : (isLogin ? 'Log In' : 'Register')}
          </motion.button>
        </motion.form>

        <p className="toggle-auth">
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <span onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? ' Register' : ' Log In'}
          </span>
        </p>
      </motion.div>
    </div>
  );
}

export default Auth;