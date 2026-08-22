"""Transactional email delivery for account verification."""

import os

import httpx
from .logging_config import logger


BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


class EmailDeliveryError(Exception):
    pass


def send_otp_email(recipient: str, otp: str) -> None:
    """Send an OTP without exposing it through the application API."""
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        raise EmailDeliveryError("BREVO_API_KEY is not configured")

    try:
        response = httpx.post(
            BREVO_EMAIL_URL,
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json={
                "sender": {
                    "name": os.getenv("BREVO_SENDER_NAME", "TaxMate AI"),
                    "email": os.getenv("BREVO_SENDER_EMAIL", "no-reply@example.com"),
                },
                "to": [{"email": recipient}],
                "subject": "Your TaxMate AI verification code",
                "textContent": f"Your TaxMate AI verification code is {otp}. It expires in 10 minutes.",
            },
            timeout=10.0,
        )
        logger.info("Brevo email response: status=%s body=%s", response.status_code, response.text)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Brevo rejected the email") from exc