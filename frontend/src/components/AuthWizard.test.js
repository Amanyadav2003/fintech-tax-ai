import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import Auth from './Auth';
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
