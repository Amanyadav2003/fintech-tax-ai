const panPattern = /(^|[^A-Z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Z0-9])/i;
const aadhaarPattern = /(^|\D)(?:\d{4}[ -]?){2}\d{4}(?!\d)/;

export const PII_FIELD_MESSAGE = "This field appears to contain a PAN or Aadhaar number, which shouldn't be entered here. Please remove it.";
export function containsPanOrAadhaar(value) {
  return Boolean(value && (panPattern.test(value) || aadhaarPattern.test(value)));
}