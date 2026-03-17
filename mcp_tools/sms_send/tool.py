"""Send an SMS message (stub — requires SMS provider configuration)."""


def run(to: str, body: str) -> str:
    """Send an SMS. Requires SMS_PROVIDER and SMS_API_KEY environment variables."""
    raise NotImplementedError(
        "sms_send requires an SMS provider API key. "
        "Set SMS_PROVIDER (twilio/vonage) and SMS_API_KEY environment variables."
    )
