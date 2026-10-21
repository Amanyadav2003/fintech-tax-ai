import { createExpenseCsv, datePart, formatExpenseDate, formatExportDate } from './ExpenseTracker';

test('formats exported expense dates for Excel', () => {
  expect(formatExportDate('2026-08-25T00:00:00')).toBe('25-08-2026');
});

test('keeps date-only expense values unchanged across timezone parsing', () => {
  expect(datePart('2026-10-21')).toBe('2026-10-21');
  expect(datePart('2026-10-21T00:00:00Z')).toBe('2026-10-21');
  expect(formatExpenseDate('2026-10-21T00:00:00Z')).toBe('21/10/2026');
  expect(formatExportDate('2026-10-21T00:00:00Z')).toBe('21-10-2026');
});

test('creates a CSV with stable headers and expense values', () => {
  const csv = createExpenseCsv([{ amount: 4500, category: 'Rent', description: 'rentav', date: '2026-08-25T00:00:00' }]);

  expect(csv).toContain('amount,category,description,date');
  expect(csv).toContain('"4500","Rent","rentav","25-08-2026"');
});