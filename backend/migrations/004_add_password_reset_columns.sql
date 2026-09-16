ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_otp_hash VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_otp_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_requested_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token_hash VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token_expires_at TIMESTAMP;