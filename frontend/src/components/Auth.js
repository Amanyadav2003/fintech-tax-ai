import React, { useState } from 'react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { Camera, CheckCircle2, Mail, ShieldCheck } from 'lucide-react';
import secureFinanceIllustration from '../assets/secure-finance.svg';

const formVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.1 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0 }
};

const shakeVariants = {
  idle: { x: 0 },
  shake: { x: [0, -6, 6, -4, 4, 0], transition: { duration: 0.4 } },
};

function Auth({ onUserCreated, onVerificationPending, initialVerification = false }) {
  const [isLogin, setIsLogin] = useState(true);
  const [isVerifying, setIsVerifying] = useState(initialVerification);
  const [otp, setOtp] = useState('');
  const [resendCountdown, setResendCountdown] = useState(0);
  const [panVerified, setPanVerified] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [registrationStarted, setRegistrationStarted] = useState(false);
  const [loginOtpPending, setLoginOtpPending] = useState(false);
  const [registrationOtpPending, setRegistrationOtpPending] = useState(false);
  const [registrationOtpVerified, setRegistrationOtpVerified] = useState(false);
  const [employmentType, setEmploymentType] = useState('');
  const [panAadhaarLinked, setPanAadhaarLinked] = useState(false);
  const [emailRemindersEnabled, setEmailRemindersEnabled] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [profilePhoto, setProfilePhoto] = useState(null);
  const [profilePhotoPreview, setProfilePhotoPreview] = useState('');
  const [panError, setPanError] = useState('');
  const [registrationSuccess, setRegistrationSuccess] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    pan: '',
    age: '',
    state: 'Maharashtra',
    employer_name: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  const passwordScore = formData.password.length === 0 ? 0 : [
    formData.password.length >= 8,
    /[A-Z]/.test(formData.password),
    /[0-9]/.test(formData.password),
    /[!@#$%^&*]/.test(formData.password)
  ].filter(Boolean).length;
  const emailReadyForOtp = !isLogin && formData.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email);
  const registrationReady = !isLogin && formData.name.trim() && formData.email && formData.password && formData.confirm_password && formData.password === formData.confirm_password && formData.phone && formData.pan && formData.age && employmentType && panAadhaarLinked && termsAccepted && panVerified && emailVerified;

  const verifyPanFormat = () => {
    const valid = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(formData.pan.toUpperCase());
    setPanVerified(valid);
    setPanError(valid ? '' : 'Expected format: ABCDE1234F (5 letters, 4 numbers, 1 letter).');
  };

  const handlePhotoChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/') || file.size > 2 * 1024 * 1024) {
      setError('Profile photo must be an image no larger than 2MB.');
      return;
    }
    setProfilePhoto(file);
    setProfilePhotoPreview(URL.createObjectURL(file));
  };

  const buildRegistrationPayload = () => ({
    email: formData.email,
    password: formData.password,
    name: formData.name,
    phone: formData.phone,
    pan: formData.pan.toUpperCase(),
    age: parseInt(formData.age),
    state: formData.state,
    employment_type: employmentType,
    pan_aadhaar_linked: panAadhaarLinked,
    financial_year: 'FY 2024-25 (AY 2025-26)',
    employer_name: formData.employer_name || null,
    email_reminders_enabled: emailRemindersEnabled,
  });

  const handleSendOtp = async (event) => {
    if (event) event.preventDefault();
    setLoading(true);
    setError('');
    setRegistrationSuccess('');
    try {
      const response = await api.post('auth/send-registration-otp', { email: formData.email });
      setRegistrationStarted(true);
      setRegistrationOtpPending(true);
      setRegistrationOtpVerified(false);
      setEmailVerified(false);
      setResendCountdown(60);
      setOtp('');
      setRegistrationSuccess(response.data.message);
      if (profilePhoto) {
        const photoData = new FormData();
        photoData.append('photo', profilePhoto);
        await api.post(`auth/registration/profile-photo?email=${encodeURIComponent(formData.email)}`, photoData, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
    } catch (err) {
      setError(getDetailedErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyRegistrationOtp = async () => {
    if (otp.length !== 6) {
      setError('Please enter the full 6-digit OTP.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await api.post('auth/verify-registration-otp', { email: formData.email, otp });
      setRegistrationOtpPending(false);
      setRegistrationOtpVerified(true);
      setEmailVerified(true);
      setOtp('');
      setRegistrationSuccess(response.data.message || 'Email verified ✓');
    } catch (err) {
      setOtp('');
      setError(getDetailedErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const finishRegistration = async () => {
    setLoading(true);
    setError('');
    try {
      await api.post('auth/register', buildRegistrationPayload());
      sessionStorage.removeItem('pending_verification_email');
      sessionStorage.setItem('user_email', formData.email);
      onUserCreated(formData.email);
    } catch (err) {
      setError(getDetailedErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

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
    if (name === 'pan') {
      setPanVerified(false);
      setPanError('');
    }
    if (name === 'email') {
      setEmailVerified(false);
      setRegistrationOtpVerified(false);
      setRegistrationOtpPending(false);
      setResendCountdown(0);
      setOtp('');
    }
    
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
      if (isVerifying && (initialVerification || loginOtpPending)) {
        const response = await api.post(initialVerification ? 'auth/verify-otp' : 'auth/login/verify-otp', { email: formData.email, otp });
        sessionStorage.removeItem('pending_verification_email');
        sessionStorage.setItem('access_token', response.data.access_token);
        sessionStorage.setItem('user_email', formData.email);
        if (initialVerification || loginOtpPending) {
          onUserCreated(formData.email);
        } else {
          setEmailVerified(true);
          setIsVerifying(false);
          setRegistrationSuccess('Email verified. Your account is ready to create.');
        }
        return;
      }

      if (isLogin) {
        const loginResponse = await api.post('auth/login', { email: formData.email, password: formData.password });
        if (loginResponse.data.access_token) {
          sessionStorage.setItem('access_token', loginResponse.data.access_token);
          sessionStorage.setItem('user_email', formData.email);
          onUserCreated(formData.email);
          return;
        }

        setLoginOtpPending(true);
        setIsVerifying(true);
        setOtp('');
        setResendCountdown(60);
        setRegistrationSuccess('A verification code has been sent to your email.');
        return;
      }

      const response = await api.post('auth/send-registration-otp', { email: formData.email });
      setRegistrationStarted(true);
      setRegistrationOtpPending(true);
      setRegistrationOtpVerified(false);
      setEmailVerified(false);
      setIsVerifying(false);
      setOtp('');
      setResendCountdown(60);
      setRegistrationSuccess(response.data.message);
      sessionStorage.setItem('pending_verification_email', formData.email);
      onVerificationPending(formData.email);

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
      const endpoint = isLogin ? 'auth/resend-otp' : 'auth/send-registration-otp';
      await api.post(endpoint, { email: formData.email });
      setResendCountdown(60);
      setRegistrationSuccess(isLogin ? 'A new login verification code has been sent.' : 'A new registration OTP has been sent.');
      if (!isLogin) {
        setRegistrationOtpPending(true);
        setRegistrationOtpVerified(false);
        setEmailVerified(false);
        setOtp('');
      }
    } catch (err) {
      setError(getDetailedErrorMessage(err));
      if (err.response?.status === 429) setResendCountdown(60);
    } finally {
      setLoading(false);
    }
  };

  if (isVerifying && (initialVerification || loginOtpPending)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-12">
        <motion.div className="fintech-card w-full max-w-md p-7 sm:p-9" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="mb-8 flex h-12 w-12 items-center justify-center rounded-xl bg-navy-50 text-navy-700"><Mail className="h-6 w-6" /></motion.div>
          <p className="text-sm font-bold uppercase tracking-[0.16em] text-navy-500">Account security</p>
          <motion.h1 animate={{ opacity: [0.8, 1, 0.8] }} transition={{ duration: 3.5, repeat: Infinity }} className="mt-2 text-3xl font-bold tracking-tight text-navy-900">Check your email</motion.h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">Enter the six-digit code sent to <span className="font-semibold text-slate-800">{formData.email}</span>.</p>
          {error && <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700" role="alert">{error}</div>}
          <form onSubmit={handleSubmit} className="mt-8">
            <motion.div variants={shakeVariants} animate={error ? 'shake' : 'idle'} className="flex justify-between gap-2" onPaste={(e) => { const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6); if (pasted) { e.preventDefault(); setOtp(pasted); document.querySelector(`[data-otp-index="${Math.min(pasted.length, 5)}"]`)?.focus(); } }}>
              {Array.from({ length: 6 }, (_, index) => (
                <motion.input key={index} data-otp-index={index} initial={{ opacity: 0, scale: 0.7, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ delay: index * 0.1, type: 'spring', stiffness: 260 }} className={`h-14 w-11 rounded-lg border-2 bg-slate-50 text-center text-xl font-bold text-navy-900 outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${error ? 'border-red-400 bg-red-50' : 'border-slate-200'} sm:w-14`} type="text" inputMode="numeric" maxLength="1" value={otp[index] || ''} onChange={(e) => { const digit = e.target.value.replace(/\D/g, '').slice(-1); const next = otp.split(''); next[index] = digit; setOtp(next.join('').slice(0, 6)); if (digit && index < 5) document.querySelector(`[data-otp-index="${index + 1}"]`)?.focus(); setError(''); }} onKeyDown={(e) => { if (e.key === 'Backspace' && !otp[index] && index > 0) document.querySelector(`[data-otp-index="${index - 1}"]`)?.focus(); }} autoFocus={index === 0} required aria-label={`Digit ${index + 1} of 6`} />
              ))}
            </motion.div>
            <button className="fintech-button mt-7 w-full" type="submit" disabled={loading || otp.length !== 6}>
              {loading ? 'Checking code...' : 'Verify email'}
            </button>
          </form>
          <div className="mt-6 flex items-center justify-center gap-4"><div className="relative h-12 w-12"><svg className="h-12 w-12 -rotate-90" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="20" fill="none" stroke="#e2e8f0" strokeWidth="3" /><circle cx="24" cy="24" r="20" fill="none" stroke="#2d5f8b" strokeWidth="3" strokeDasharray="125.66" strokeDashoffset={resendCountdown ? `${125.66 * (resendCountdown / 60)}` : 0} strokeLinecap="round" /></svg>{resendCountdown > 0 && <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-navy-700">{resendCountdown}</span>}</div><button className="text-sm font-semibold text-navy-700 transition hover:text-navy-900 disabled:cursor-not-allowed disabled:text-slate-400" type="button" onClick={handleResend} disabled={loading || resendCountdown > 0}>{resendCountdown > 0 ? 'Wait before resending' : 'Resend code'}</button></div>
          <motion.div initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.7, type: 'spring' }} className="mt-6 flex items-center justify-center gap-2 text-xs font-medium text-mint-700"><CheckCircle2 className="h-4 w-4" /> Verification is secure</motion.div>
          <p className="mt-6 text-center text-sm text-slate-500"><span className="cursor-pointer font-semibold text-navy-700 hover:text-navy-900" onClick={() => { setIsVerifying(false); setIsLogin(true); setError(''); }}>Use a different account</span></p>
        </motion.div>
      </div>
    );
  }

  return (
      <div className="flex min-h-screen items-center justify-center bg-transparent px-5 py-12">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft lg:grid-cols-2">
      <motion.div 
        className="p-7 sm:p-9 lg:p-12"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <p className="text-sm font-bold uppercase tracking-[0.16em] text-navy-500">TaxMate AI</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-navy-900">{isLogin ? 'Welcome back' : 'Create your account'}</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{isLogin ? 'Log in to access your personal tax workspace.' : 'Set up your secure workspace in a few minutes.'}</p>
        
        {error && <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700" role="alert">{error}</div>}
        {registrationSuccess && <div className="mt-6 rounded-lg border border-mint-500/30 bg-mint-50 px-4 py-3 text-sm font-medium text-mint-700" role="status">{registrationSuccess}</div>}

        <motion.form className="mt-7 space-y-4 text-left" onSubmit={isLogin ? handleSubmit : handleSendOtp} variants={formVariants} initial="hidden" animate={error ? 'shake' : 'visible'}>
          {!isLogin && (
            <>
              <motion.div variants={itemVariants} className="form-group">
                <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="name">Full name</label><input id="name" type="text" name="name" placeholder="Amaan S. Yadav" value={formData.name} onChange={handleChange} required className={`w-full rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${fieldErrors.name ? 'border-red-400' : 'border-slate-200'}`} />
                {fieldErrors.name && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.name}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="pan">PAN card</label><div className="flex gap-2"><input id="pan" type="text" name="pan" placeholder="ABCDE1234F" value={formData.pan} onChange={handleChange} required maxLength="10" className={`min-w-0 flex-1 rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm uppercase outline-none focus:border-navy-500 ${fieldErrors.pan || panError ? 'border-red-400' : panVerified ? 'border-mint-500' : 'border-slate-200'}`} /><button type="button" onClick={verifyPanFormat} className="rounded-lg bg-navy-50 px-3 text-xs font-bold text-navy-700">Verify</button></div>{panVerified && <motion.p initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-1 flex items-center gap-1 text-xs font-semibold text-mint-700"><CheckCircle2 className="h-3.5 w-3.5" /> Format verified</motion.p>}{panError && <p className="mt-1 text-xs font-medium text-red-600">{panError}</p>}<p className="mt-1 text-xs text-slate-500">Structural format check only; this does not verify PAN details with a government database.</p>
                {fieldErrors.pan && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.pan}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="phone">Phone number</label><input id="phone" type="tel" name="phone" placeholder="9876543210" value={formData.phone} onChange={handleChange} required className={`w-full rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${fieldErrors.phone ? 'border-red-400' : 'border-slate-200'}`} />
                {fieldErrors.phone && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.phone}</div>}
              </motion.div>

              <motion.div variants={itemVariants} className="form-group">
                <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="age">Age</label><input id="age" type="number" name="age" placeholder="30" value={formData.age} onChange={handleChange} required className={`w-full rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${fieldErrors.age ? 'border-red-400' : 'border-slate-200'}`} />
                {fieldErrors.age && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.age}</div>}
              </motion.div>
            </>
          )}

          <motion.div variants={itemVariants} className="form-group">
            <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="email">Email address</label>
            <div className="flex gap-2"><input id="email" type="email" name="email" placeholder="you@example.com" value={formData.email} onChange={handleChange} required className={`min-w-0 flex-1 rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${fieldErrors.email ? 'border-red-400' : 'border-slate-200'}`} />{!isLogin && <button type="button" className="rounded-lg bg-navy-50 px-3 text-xs font-bold text-navy-700 disabled:cursor-not-allowed disabled:opacity-50" onClick={handleSendOtp} disabled={!emailReadyForOtp || loading || registrationOtpPending}>{registrationOtpVerified ? 'Verified' : registrationOtpPending ? 'Sent' : 'Send OTP'}</button>}</div>
            {fieldErrors.email && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.email}</div>}
            {!isLogin && !registrationOtpPending && !registrationOtpVerified && <p className="mt-1 text-xs text-slate-500">Enter a valid email to begin registration OTP verification.</p>}
            {!isLogin && (registrationOtpPending || registrationOtpVerified) && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-4 rounded-xl border border-navy-100 bg-navy-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-navy-900"><Mail className="h-4 w-4 text-navy-500" />{registrationOtpVerified ? 'Email verified ✓' : 'Check your email'}</div>
                <p className="mt-1 text-xs text-slate-600">Enter the 6-digit code sent to {formData.email}.</p>
                <motion.div variants={shakeVariants} animate={error ? 'shake' : 'idle'} className="mt-3 flex gap-2" onPaste={(e) => { const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6); if (pasted) { e.preventDefault(); setOtp(pasted); } }}>
                  {Array.from({ length: 6 }, (_, index) => (
                    <input key={index} data-otp-index={index} disabled={registrationOtpVerified} className={`h-11 w-11 rounded-lg border-2 bg-white text-center text-lg font-bold text-navy-900 outline-none ${error ? 'border-red-400 bg-red-50' : registrationOtpVerified ? 'border-mint-500' : 'border-slate-200'} ${registrationOtpVerified ? 'cursor-default' : ''}`} type="text" inputMode="numeric" maxLength="1" value={otp[index] || ''} onChange={(e) => { const digit = e.target.value.replace(/\D/g, '').slice(-1); const next = otp.split(''); next[index] = digit; setOtp(next.join('').slice(0, 6)); if (digit && index < 5) document.querySelector(`[data-otp-index="${index + 1}"]`)?.focus(); setError(''); }} onKeyDown={(e) => { if (e.key === 'Backspace' && !otp[index] && index > 0) document.querySelector(`[data-otp-index="${index - 1}"]`)?.focus(); }} autoFocus={index === 0} aria-label={`Digit ${index + 1} of 6`} />
                  ))}
                </motion.div>
                <div className="mt-3 flex items-center justify-between gap-3">
                  <button type="button" onClick={handleVerifyRegistrationOtp} disabled={loading || otp.length !== 6 || registrationOtpVerified} className="fintech-button px-4 py-2 text-xs disabled:opacity-60">{registrationOtpVerified ? 'Verified' : 'Verify OTP'}</button>
                  <div className="flex items-center gap-2">
                    <div className="relative h-9 w-9"><svg className="h-9 w-9 -rotate-90" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="20" fill="none" stroke="#dbe5ef" strokeWidth="3" /><circle cx="24" cy="24" r="20" fill="none" stroke="#2d5f8b" strokeWidth="3" strokeDasharray="125.66" strokeDashoffset={resendCountdown ? `${125.66 * (resendCountdown / 60)}` : 0} strokeLinecap="round" /></svg>{resendCountdown > 0 && <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-navy-700">{resendCountdown}</span>}</div>
                    <button type="button" onClick={handleResend} disabled={loading || resendCountdown > 0} className="text-xs font-semibold text-navy-700 disabled:cursor-not-allowed disabled:text-slate-400">{resendCountdown > 0 ? `Resend in ${resendCountdown}s` : 'Resend OTP'}</button>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>

          <motion.div variants={itemVariants} className="form-group">
            <label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="password">Password</label><input id="password" type="password" name="password" placeholder="Your secure password" value={formData.password} onChange={handleChange} required className={`w-full rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-navy-500 focus:bg-white focus:ring-4 focus:ring-navy-100 ${fieldErrors.password ? 'border-red-400' : 'border-slate-200'}`} />
            {fieldErrors.password && <div className="mt-1 text-xs font-medium text-red-600">{fieldErrors.password}</div>}
          </motion.div>
          {!isLogin && <motion.div variants={itemVariants} className="form-group"><label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="confirm_password">Confirm password</label><input id="confirm_password" type="password" name="confirm_password" placeholder="Repeat your password" value={formData.confirm_password} onChange={handleChange} required className={`w-full rounded-lg border-2 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-navy-500 ${formData.confirm_password && formData.confirm_password !== formData.password ? 'border-red-400' : 'border-slate-200'}`} />{formData.confirm_password && formData.confirm_password !== formData.password && <div className="mt-1 text-xs font-medium text-red-600">Passwords do not match</div>}</motion.div>}
          
          {!isLogin && (
            <motion.div variants={itemVariants} className="text-xs text-slate-500">
              <div className="mb-1 flex justify-between"><span>Password strength</span><span className={passwordScore >= 4 ? 'text-mint-700' : passwordScore >= 2 ? 'text-amber-600' : 'text-red-600'}>{passwordScore >= 4 ? 'Strong' : passwordScore >= 2 ? 'Medium' : 'Weak'}</span></div><div className="flex h-1.5 gap-1"><span className={`flex-1 rounded-full ${passwordScore >= 1 ? 'bg-red-500' : 'bg-slate-200'}`} /><span className={`flex-1 rounded-full ${passwordScore >= 2 ? 'bg-amber-500' : 'bg-slate-200'}`} /><span className={`flex-1 rounded-full ${passwordScore >= 4 ? 'bg-mint-500' : 'bg-slate-200'}`} /></div><p className="mt-2">Must include uppercase letter, number, and special character.</p>
            </motion.div>
          )}

          {!isLogin && <>
            <motion.div variants={itemVariants} className="form-group"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Employment type</span><div className="flex flex-wrap gap-4">{['Salaried', 'Self-employed', 'Business'].map(option => <label key={option} className="flex items-center gap-2 text-sm text-slate-600"><input type="radio" name="employment_type" value={option} checked={employmentType === option} onChange={(e) => setEmploymentType(e.target.value)} />{option}</label>)}</div></motion.div>
            <motion.div variants={itemVariants} className="form-group"><label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="financial_year">Financial year</label><select id="financial_year" value="FY 2024-25 (AY 2025-26)" disabled className="w-full rounded-lg border-2 border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-600"><option>FY 2024-25 (AY 2025-26)</option></select></motion.div>
            <motion.div variants={itemVariants} className="form-group"><label className="mb-1.5 block text-sm font-semibold text-slate-700" htmlFor="employer_name">Employer / company name <span className="font-normal text-slate-400">(optional)</span></label><input id="employer_name" type="text" name="employer_name" maxLength="150" placeholder="Your company" value={formData.employer_name} onChange={handleChange} className="w-full rounded-lg border-2 border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-navy-500" /></motion.div>
            <motion.div variants={itemVariants}><label className="flex items-start gap-3 text-sm leading-6 text-slate-600"><input type="checkbox" checked={panAadhaarLinked} onChange={(e) => setPanAadhaarLinked(e.target.checked)} className="mt-1" /> <span>My PAN is linked with Aadhaar as required by the Income Tax Department.<span className="block text-xs text-slate-400">Self-declaration only; no government database verification is performed.</span></span></label></motion.div>
            <motion.div variants={itemVariants}><label className="flex items-center gap-3 text-sm text-slate-600"><input type="checkbox" checked={emailRemindersEnabled} onChange={(e) => setEmailRemindersEnabled(e.target.checked)} />Notify me about tax filing deadlines and updates</label></motion.div>
            <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-3"><div className="relative h-20 w-20 overflow-hidden rounded-full border-2 border-slate-200 bg-slate-100">{profilePhotoPreview ? <img src={profilePhotoPreview} alt="Profile preview" className="h-full w-full object-cover" /> : <div className="flex h-full items-center justify-center text-2xl">👤</div>}<Camera className="absolute bottom-0 right-0 rounded-full bg-navy-700 p-1 text-white" size={24} /></div><label className="cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-navy-700">Take Photo<input type="file" accept="image/*" capture="environment" onChange={handlePhotoChange} className="hidden" /></label><label className="cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-navy-700">Choose from Gallery<input type="file" accept="image/*" onChange={handlePhotoChange} className="hidden" /></label><span className="w-full text-xs text-slate-500">Optional. Images only, maximum 2MB.</span></motion.div>
            {registrationStarted && <motion.div variants={itemVariants} className="rounded-xl border border-navy-100 bg-navy-50 p-4"><div className="flex items-center gap-2 text-sm font-semibold text-navy-900"><motion.span animate={{ scale: [1, 1.08, 1] }} transition={{ duration: 2.5, repeat: Infinity }}><Mail className="h-4 w-4 text-navy-500" /></motion.span>Check your email</div><p className="mt-1 text-xs text-slate-600">Enter the 6-digit code sent to {formData.email}.</p><div className="mt-3 flex gap-1.5">{Array.from({ length: 6 }, (_, index) => <motion.input key={index} data-inline-otp-index={index} initial={{ opacity: 0, scale: 0.7 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: index * 0.1 }} className={`h-10 w-10 rounded-lg border-2 bg-white text-center font-bold text-navy-900 outline-none ${error ? 'border-red-400 bg-red-50' : emailVerified ? 'border-mint-500' : 'border-slate-200'}`} value={otp[index] || ''} maxLength="1" inputMode="numeric" onChange={(e) => { const digit = e.target.value.replace(/\D/g, '').slice(-1); const next = otp.split(''); next[index] = digit; setOtp(next.join('').slice(0, 6)); if (digit && index < 5) document.querySelector(`[data-inline-otp-index="${index + 1}"]`)?.focus(); setError(''); }} aria-label={`OTP digit ${index + 1}`} />)}</div><div className="mt-3 flex items-center gap-3"><button type="button" onClick={handleSubmit} disabled={loading || otp.length !== 6 || emailVerified} className="fintech-button px-4 py-2 text-xs">{emailVerified ? <><CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Email verified</> : 'Verify email'}</button><div className="relative h-9 w-9"><svg className="h-9 w-9 -rotate-90" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="20" fill="none" stroke="#dbe5ef" strokeWidth="3" /><circle cx="24" cy="24" r="20" fill="none" stroke="#2d5f8b" strokeWidth="3" strokeDasharray="125.66" strokeDashoffset={resendCountdown ? `${125.66 * (resendCountdown / 60)}` : 0} strokeLinecap="round" /></svg>{resendCountdown > 0 && <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-navy-700">{resendCountdown}</span>}</div><button type="button" onClick={handleResend} disabled={loading || resendCountdown > 0 || emailVerified} className="text-xs font-semibold text-navy-700 disabled:text-slate-400">{resendCountdown > 0 ? 'Resend later' : 'Resend OTP'}</button></div></motion.div>}
            <motion.div variants={itemVariants}><label className="flex items-start gap-3 text-sm leading-6 text-slate-600"><input type="checkbox" checked={termsAccepted} onChange={(e) => setTermsAccepted(e.target.checked)} className="mt-1" /> <span>I agree to the <a className="font-semibold text-navy-700" href="/terms">Terms of Service</a> and <a className="font-semibold text-navy-700" href="/privacy">Privacy Policy</a>.</span></label></motion.div>
          </>}
          
          <motion.button 
            className="fintech-button w-full" 
            type={isLogin ? 'submit' : 'button'} 
            disabled={loading || (!isLogin && (!registrationReady || !emailVerified))}
            onClick={isLogin ? undefined : finishRegistration}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? 'Please wait...' : (isLogin ? 'Log in' : 'Create account')}
          </motion.button>
        </motion.form>

        <p className="mt-7 text-center text-sm text-slate-500">
          {isLogin ? "Don't have an account?" : "Already have an account?"} <span className="cursor-pointer font-semibold text-navy-700 hover:text-navy-900" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? ' Register' : ' Log In'}
          </span>
        </p>
      </motion.div>
      <div className="hidden bg-navy-50 p-10 lg:flex lg:flex-col lg:justify-center"><div className="max-w-sm"><div className="mb-8 inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-navy-700"><ShieldCheck className="h-4 w-4 text-mint-700" /> Secure workspace</div><h2 className="text-3xl font-bold leading-tight text-navy-900">Your financial picture, protected.</h2><p className="mt-4 leading-7 text-slate-600">A focused workspace for making better tax decisions with confidence.</p><img src={secureFinanceIllustration} alt="Person reviewing a secure financial dashboard" className="mt-8 w-full" /></div></div>
      </div>
    </div>
  );
}

export default Auth;