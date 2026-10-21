import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import Auth, { isValidGoogleClientId } from './Auth';
import api from '../services/api';

jest.mock('../services/api', () => ({
  __esModule: true,
  default: { post: jest.fn() },
}));

const fillStepOne = () => {
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Amaan Yadav' } });
  fireEvent.change(screen.getByLabelText('PAN card'), { target: { value: 'ABCDE1234F' } });
  fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: '9876543210' } });
  fireEvent.change(screen.getByLabelText('Age'), { target: { value: '30' } });
};

const moveToFinish = async () => {
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fillStepOne();
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));

  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'amaan@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'TaxMate!23' } });
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'TaxMate!23' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send OTP' }));

  await waitFor(() => expect(api.post).toHaveBeenCalledWith('auth/send-registration-otp', { email: 'amaan@example.com' }));
  screen.getAllByLabelText(/Digit \d of 6/).forEach((input, index) => {
    fireEvent.input(input, { target: { value: String(index + 1) } });
  });
  fireEvent.click(screen.getByRole('button', { name: 'Verify OTP' }));
  await waitFor(() => expect(screen.getAllByRole('button', { name: 'Verified' })).toHaveLength(2));

  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  fireEvent.click(screen.getByLabelText('Salaried'));
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
};

beforeEach(() => {
  api.post.mockReset();
  api.post.mockImplementation(endpoint => Promise.resolve({
    data: { message: endpoint === 'auth/register' ? 'Registered' : 'Email verified' },
  }));
  sessionStorage.clear();
});

beforeAll(() => {
  window.scrollTo = jest.fn();
});

test('renders the existing login and registration UI without Google configuration', () => {
  const originalClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  delete process.env.REACT_APP_GOOGLE_CLIENT_ID;
  const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});

  const { unmount } = render(<Auth onUserCreated={jest.fn()} />);
  expect(screen.getByRole('button', { name: 'Log in' })).toBeTruthy();
  expect(screen.queryByTestId('google-signin')).toBeNull();
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  expect(screen.getByLabelText('Full name')).toBeTruthy();
  expect(screen.queryByTestId('google-signin')).toBeNull();
  expect(warn).toHaveBeenCalledTimes(1);
  unmount();

  if (originalClientId !== undefined) process.env.REACT_APP_GOOGLE_CLIENT_ID = originalClientId;
  warn.mockRestore();
});

test('moves from valid personal details to account security', () => {
  render(<Auth onUserCreated={jest.fn()} />);
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fillStepOne();

  fireEvent.click(screen.getByRole('button', { name: 'Next' }));

  expect(screen.getByText('Step 2 of 4')).toBeTruthy();
  expect(screen.getByText('Account security')).toBeTruthy();
});

test('shows the existing validation message and stays on personal details', () => {
  render(<Auth onUserCreated={jest.fn()} />);
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'A' } });

  fireEvent.click(screen.getByRole('button', { name: 'Next' }));

  expect(screen.getByText('Step 1 of 4')).toBeTruthy();
  expect(screen.getByRole('alert').textContent).toBe('Must be at least 2 characters long.');
});

test('Back preserves entered personal details', () => {
  render(<Auth onUserCreated={jest.fn()} />);
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fillStepOne();
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  fireEvent.click(screen.getByRole('button', { name: 'Back' }));

  expect(screen.getByLabelText('Full name').value).toBe('Amaan Yadav');
  expect(screen.getByLabelText('PAN card').value).toBe('ABCDE1234F');
});

test('Create account remains disabled until terms are accepted', async () => {
  render(<Auth onUserCreated={jest.fn()} />);
  await moveToFinish();

  const createAccount = screen.getByRole('button', { name: 'Create account' });
  const checkboxes = screen.getAllByRole('checkbox');
  expect(createAccount.disabled).toBe(true);

  fireEvent.click(checkboxes[0]);
  expect(createAccount.disabled).toBe(true);
  fireEvent.click(checkboxes[2]);
  expect(createAccount.disabled).toBe(false);
});

test('submits the unchanged registration payload exactly once', async () => {
  const onUserCreated = jest.fn();
  render(<Auth onUserCreated={onUserCreated} />);
  await moveToFinish();
  fireEvent.click(screen.getAllByRole('checkbox')[0]);
  fireEvent.click(screen.getAllByRole('checkbox')[2]);

  fireEvent.click(screen.getByRole('button', { name: 'Create account' }));

  await waitFor(() => {
    const registrationCalls = api.post.mock.calls.filter(([endpoint]) => endpoint === 'auth/register');
    expect(registrationCalls).toHaveLength(1);
    expect(registrationCalls[0][1]).toEqual({
      email: 'amaan@example.com',
      password: 'TaxMate!23',
      name: 'Amaan Yadav',
      phone: '9876543210',
      pan: 'ABCDE1234F',
      age: 30,
      state: 'Maharashtra',
      employment_type: 'Salaried',
      pan_aadhaar_linked: true,
      financial_year: 'FY 2025-26 (AY 2026-27)',
      employer_name: null,
      email_reminders_enabled: true,
    });
  });
  expect(onUserCreated).toHaveBeenCalledTimes(1);
  expect(onUserCreated).toHaveBeenCalledWith('amaan@example.com');
});

test('renders the configured Google sign-in option on Login and Register', async () => {
  const originalClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  const originalGoogle = window.google;
  const renderButton = jest.fn();
  const initialize = jest.fn();
  const getClientRects = jest.spyOn(HTMLElement.prototype, 'getClientRects')
    .mockImplementation(function getClientRectsForGoogleButton() {
      return this.dataset?.testid === 'google-signin' ? [{}] : [];
    });
  const getBoundingClientRect = jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect')
    .mockImplementation(function getGoogleButtonBounds() {
      return this.dataset?.testid === 'google-signin' ? { width: 320 } : { width: 0 };
    });
  process.env.REACT_APP_GOOGLE_CLIENT_ID = '123456789012-test.apps.googleusercontent.com';
  window.google = { accounts: { id: { initialize, renderButton } } };

  try {
    render(<Auth onUserCreated={jest.fn()} />);
    await waitFor(() => expect(renderButton).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('google-signin')).toBeTruthy();

    fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
    await waitFor(() => expect(renderButton).toHaveBeenCalledTimes(2));
    expect(screen.getByTestId('google-signin')).toBeTruthy();
    expect(initialize).toHaveBeenCalledWith(expect.objectContaining({
      client_id: '123456789012-test.apps.googleusercontent.com',
      ux_mode: 'popup',
    }));
    expect(renderButton).toHaveBeenLastCalledWith(
      screen.getByTestId('google-signin'),
      expect.objectContaining({ theme: 'filled_black', text: 'continue_with', width: 320 })
    );
  } finally {
    getClientRects.mockRestore();
    getBoundingClientRect.mockRestore();
    if (originalClientId === undefined) delete process.env.REACT_APP_GOOGLE_CLIENT_ID;
    else process.env.REACT_APP_GOOGLE_CLIENT_ID = originalClientId;
    if (originalGoogle === undefined) delete window.google;
    else window.google = originalGoogle;
  }
});

test('only accepts a Google Web OAuth client ID format', () => {
  expect(isValidGoogleClientId('123456789012-test.apps.googleusercontent.com')).toBe(true);
  expect(isValidGoogleClientId('not-a-client-id')).toBe(false);
  expect(isValidGoogleClientId('123456789012-test.apps.googleusercontent.com.evil.test')).toBe(false);
});

test('shows a configuration error for an invalid non-empty Google client ID', () => {
  const originalClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  process.env.REACT_APP_GOOGLE_CLIENT_ID = 'invalid-client-id';

  try {
    render(<Auth onUserCreated={jest.fn()} />);
    expect(screen.getByRole('alert').textContent).toContain('Google sign-in is unavailable because the OAuth client ID is invalid.');
    fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
    expect(screen.getByRole('alert').textContent).toContain('Google sign-in is unavailable because the OAuth client ID is invalid.');
    expect(screen.queryByTestId('google-signin')).toBeNull();
  } finally {
    if (originalClientId === undefined) delete process.env.REACT_APP_GOOGLE_CLIENT_ID;
    else process.env.REACT_APP_GOOGLE_CLIENT_ID = originalClientId;
  }
});

test('keeps registration fields visible and shows an incorrect OTP inline', async () => {
  api.post.mockImplementation(endpoint => {
    if (endpoint === 'auth/verify-registration-otp') {
      return Promise.reject({ response: { status: 400, data: { detail: 'Incorrect OTP' } } });
    }
    return Promise.resolve({ data: { message: 'Registration OTP sent to your email.' } });
  });

  render(<Auth onUserCreated={jest.fn()} />);
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fillStepOne();
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'amaan@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'TaxMate!23' } });
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'TaxMate!23' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send OTP' }));

  await waitFor(() => expect(screen.getByText('Registration OTP sent to your email.')).toBeTruthy());
  screen.getAllByLabelText(/Digit \d of 6/).forEach((input, index) => {
    fireEvent.input(input, { target: { value: String(index + 1) } });
  });
  fireEvent.click(screen.getByRole('button', { name: 'Verify OTP' }));

  await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('Incorrect OTP. Please enter the correct OTP and try again.'));
  expect(screen.getByLabelText('Email address')).toBeTruthy();
  expect(screen.getByLabelText('Password')).toBeTruthy();
  expect(screen.getByLabelText('Confirm password')).toBeTruthy();
  expect(screen.queryByText('Registration OTP sent to your email.')).toBeNull();
  expect(document.activeElement).toBe(screen.getByLabelText('Digit 1 of 6'));

  fireEvent.click(screen.getByRole('tab', { name: 'Login' }));
  expect(screen.queryByText('Incorrect OTP. Please enter the correct OTP and try again.')).toBeNull();
  expect(screen.queryByText('Registration OTP sent to your email.')).toBeNull();
});

test('clears registration OTP messages when the wizard step changes', async () => {
  api.post.mockResolvedValue({ data: { message: 'Registration OTP sent to your email.' } });

  render(<Auth onUserCreated={jest.fn()} />);
  fireEvent.click(screen.getByRole('tab', { name: 'Register' }));
  fillStepOne();
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'amaan@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'TaxMate!23' } });
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'TaxMate!23' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send OTP' }));

  await waitFor(() => expect(screen.getByText('Registration OTP sent to your email.')).toBeTruthy());
  fireEvent.click(screen.getByRole('button', { name: 'Back' }));
  expect(screen.queryByText('Registration OTP sent to your email.')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  expect(screen.queryByText('Registration OTP sent to your email.')).toBeNull();
});
