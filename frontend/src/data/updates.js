export const CURRENT_VERSION = '1.1.0';
export const UPDATE_READ_KEY = 'taxmate-latest-update-read';
export const UPDATE_READ_EVENT = 'taxmate:update-read';

export const updates = [
  {
    version: '1.1.0',
    releaseDate: 'August 2026',
    title: 'A clearer tax workspace',
    description: 'TaxMate AI now makes filing progress, records, and guidance easier to review in one focused workspace.',
    newFeatures: [
      { title: 'Document Vault', description: 'Store supported tax documents securely and review extracted filing values.' },
      { title: 'Expense Tracker', description: 'Keep a personal record of tax-relevant expenses with category summaries.' },
      { title: 'TaxMate chat assistant', description: 'Ask tax-focused questions with saved conversation history.' },
      { title: 'Analysis History', description: 'Review completed filing analyses and compare previous results.' },
    ],
    improvements: [
      { title: 'Multi-agent tax analysis', description: 'Tax, risk, and strategy guidance now appears together with a transparency panel.' },
      { title: 'OTP-based account verification', description: 'Registration and login verification provide stronger account protection.' },
    ],
    fixes: [
      { title: 'Tax calculation accuracy', description: 'Health and education cess and Section 87A rebate handling are corrected.' },
    ],
  },
  {
    version: '1.0.0',
    releaseDate: 'July 2026',
    title: 'TaxMate AI launches',
    description: 'The first TaxMate AI release brings guided tax analysis and practical filing support together.',
    newFeatures: [
      { title: 'Guided tax analysis', description: 'Work through income and deductions before reviewing a filing recommendation.' },
    ],
    improvements: [],
    fixes: [],
  },
];

export const latestUpdate = updates[0];

export function isUpdateUnread() {
  return localStorage.getItem(UPDATE_READ_KEY) !== latestUpdate.version;
}

export function markLatestUpdateRead() {
  localStorage.setItem(UPDATE_READ_KEY, latestUpdate.version);
  window.dispatchEvent(new Event(UPDATE_READ_EVENT));
}
