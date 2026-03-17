"""Reply to an email message (stub — requires SMTP/IMAP configuration)."""


def run(id: str, body: str) -> str:
    """Reply to an email. Requires SMTP_HOST, SMTP_USER, SMTP_PASS environment variables."""
    raise NotImplementedError(
        "email_reply requires SMTP configuration. "
        "Set SMTP_HOST, SMTP_USER, SMTP_PASS, IMAP_HOST environment variables."
    )
