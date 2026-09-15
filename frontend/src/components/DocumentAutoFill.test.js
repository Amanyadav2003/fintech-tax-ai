import { combineConfirmedDocumentValues } from './Documents';
import { mergeDocumentValues } from './DeductionForm';

const documents = [
  { id: 1, document_type: '80c' },
  { id: 2, document_type: '80c' },
];

const draftValues = {
  1: { investments_80c: 25000 },
  2: { investments_80c: 40000 },
};

const confirmed = { 1: true, 2: true };

test('combines distinct 80C documents once and stays stable when reapplied', () => {
  const applied = combineConfirmedDocumentValues(documents, draftValues, confirmed);

  expect(applied.investments_80c).toBe(65000);
  expect(combineConfirmedDocumentValues(documents, draftValues, confirmed)).toEqual(applied);
});

test('reopening and editing the deduction form does not double-count document values', () => {
  const applied = combineConfirmedDocumentValues(documents, draftValues, confirmed);
  const reopened = mergeDocumentValues({}, applied);
  const manuallyEdited = { ...reopened, investments_80c: 70000 };
  const nextRenderWithUnchangedDocuments = mergeDocumentValues(manuallyEdited, {});

  expect(reopened.investments_80c).toBe(65000);
  expect(nextRenderWithUnchangedDocuments.investments_80c).toBe(70000);
});