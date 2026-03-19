"""Unified email management: send, fetch, read, reply, and search emails.

Uses imaplib/smtplib for email operations. Requires environment variables:
  ARQITECT_SMTP_HOST, ARQITECT_SMTP_USER, ARQITECT_SMTP_PASS,
  ARQITECT_IMAP_HOST, ARQITECT_IMAP_USER, ARQITECT_IMAP_PASS
Returns descriptive errors if not configured.
"""

import email
import email.utils
import imaplib
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText

VALID_OPERATIONS = {"send", "fetch", "read", "reply", "search"}

SMTP_HOST = os.environ.get("ARQITECT_SMTP_HOST", "")
SMTP_USER = os.environ.get("ARQITECT_SMTP_USER", "")
SMTP_PASS = os.environ.get("ARQITECT_SMTP_PASS", "")
SMTP_PORT = int(os.environ.get("ARQITECT_SMTP_PORT", "587"))
IMAP_HOST = os.environ.get("ARQITECT_IMAP_HOST", "")
IMAP_USER = os.environ.get("ARQITECT_IMAP_USER", "")
IMAP_PASS = os.environ.get("ARQITECT_IMAP_PASS", "")


def _check_smtp_config() -> None:
    """Verify SMTP environment variables are set.

    Raises:
        RuntimeError: If any required SMTP env var is missing.
    """
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        raise RuntimeError(
            "SMTP not configured. Set ARQITECT_SMTP_HOST, ARQITECT_SMTP_USER, "
            "and ARQITECT_SMTP_PASS environment variables."
        )


def _check_imap_config() -> None:
    """Verify IMAP environment variables are set.

    Raises:
        RuntimeError: If any required IMAP env var is missing.
    """
    if not IMAP_HOST or not IMAP_USER or not IMAP_PASS:
        raise RuntimeError(
            "IMAP not configured. Set ARQITECT_IMAP_HOST, ARQITECT_IMAP_USER, "
            "and ARQITECT_IMAP_PASS environment variables."
        )


def _connect_imap() -> imaplib.IMAP4_SSL:
    """Connect and authenticate to the IMAP server.

    Returns:
        Authenticated IMAP4_SSL connection.
    """
    _check_imap_config()
    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    conn.login(IMAP_USER, IMAP_PASS)
    return conn


def _handle_send(params: dict) -> dict:
    """Send an email.

    Args:
        params: Must contain 'to', 'subject', and 'body'.

    Returns:
        Dict with status and message details.
    """
    _check_smtp_config()

    to_addr = params.get("to")
    subject = params.get("subject")
    body = params.get("body")

    if not to_addr:
        raise ValueError("to is required for send operation")
    if not subject:
        raise ValueError("subject is required for send operation")
    if not body:
        raise ValueError("body is required for send operation")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    msg["Date"] = email.utils.formatdate(localtime=True)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    return {"status": "sent", "to": to_addr, "subject": subject}


def _handle_fetch(params: dict) -> dict:
    """Fetch recent emails from a mailbox folder.

    Args:
        params: Optionally contains 'folder', 'count', and 'filter_str'.

    Returns:
        Dict with list of email summaries.
    """
    folder = params.get("folder", "INBOX")
    count = int(params.get("count", "10"))
    filter_str = params.get("filter_str", "ALL")

    conn = _connect_imap()
    try:
        conn.select(folder, readonly=True)
        _, msg_nums = conn.search(None, filter_str)
        ids = msg_nums[0].split()
        ids = ids[-count:] if len(ids) > count else ids

        messages = []
        for msg_id in ids:
            _, data = conn.fetch(msg_id, "(RFC822)")
            raw = data[0][1]
            parsed = email.message_from_bytes(raw)
            messages.append({
                "id": msg_id.decode(),
                "from": parsed.get("From", ""),
                "subject": parsed.get("Subject", ""),
                "date": parsed.get("Date", ""),
            })
        return {"status": "ok", "folder": folder, "count": len(messages), "messages": messages}
    finally:
        conn.logout()


def _handle_read(params: dict) -> dict:
    """Read a specific email by ID.

    Args:
        params: Must contain 'id'. Optionally 'folder'.

    Returns:
        Dict with full email content.
    """
    msg_id = params.get("id")
    if not msg_id:
        raise ValueError("id is required for read operation")

    folder = params.get("folder", "INBOX")

    conn = _connect_imap()
    try:
        conn.select(folder, readonly=True)
        _, data = conn.fetch(msg_id.encode(), "(RFC822)")
        raw = data[0][1]
        parsed = email.message_from_bytes(raw)

        body = ""
        if parsed.is_multipart():
            for part in parsed.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = parsed.get_payload(decode=True).decode("utf-8", errors="replace")

        return {
            "status": "ok",
            "id": msg_id,
            "from": parsed.get("From", ""),
            "to": parsed.get("To", ""),
            "subject": parsed.get("Subject", ""),
            "date": parsed.get("Date", ""),
            "body": body,
        }
    finally:
        conn.logout()


def _handle_reply(params: dict) -> dict:
    """Reply to an email message.

    Args:
        params: Must contain 'id' and 'body'. Optionally 'folder'.

    Returns:
        Dict with status and reply details.
    """
    _check_smtp_config()

    msg_id = params.get("id")
    body = params.get("body")
    if not msg_id:
        raise ValueError("id is required for reply operation")
    if not body:
        raise ValueError("body is required for reply operation")

    folder = params.get("folder", "INBOX")

    conn = _connect_imap()
    try:
        conn.select(folder, readonly=True)
        _, data = conn.fetch(msg_id.encode(), "(RFC822)")
        raw = data[0][1]
        original = email.message_from_bytes(raw)
    finally:
        conn.logout()

    reply_to = original.get("Reply-To") or original.get("From", "")
    subject = original.get("Subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = reply_to
    msg["In-Reply-To"] = original.get("Message-ID", "")
    msg["References"] = original.get("Message-ID", "")
    msg["Date"] = email.utils.formatdate(localtime=True)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    return {"status": "replied", "to": reply_to, "subject": subject}


def _handle_search(params: dict) -> dict:
    """Search emails using an IMAP search query.

    Args:
        params: Must contain 'query'. Optionally 'folder'.

    Returns:
        Dict with list of matching email summaries.
    """
    query = params.get("query")
    if not query:
        raise ValueError("query is required for search operation")

    folder = params.get("folder", "INBOX")

    conn = _connect_imap()
    try:
        conn.select(folder, readonly=True)
        # Build IMAP search criterion from plain text query
        search_criterion = f'(OR SUBJECT "{query}" FROM "{query}")'
        _, msg_nums = conn.search(None, search_criterion)
        ids = msg_nums[0].split()

        messages = []
        for msg_id in ids[-50:]:
            _, data = conn.fetch(msg_id, "(RFC822)")
            raw = data[0][1]
            parsed = email.message_from_bytes(raw)
            messages.append({
                "id": msg_id.decode(),
                "from": parsed.get("From", ""),
                "subject": parsed.get("Subject", ""),
                "date": parsed.get("Date", ""),
            })
        return {"status": "ok", "query": query, "count": len(messages), "messages": messages}
    finally:
        conn.logout()


HANDLERS = {
    "send": _handle_send,
    "fetch": _handle_fetch,
    "read": _handle_read,
    "reply": _handle_reply,
    "search": _handle_search,
}


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        operation = params.get("operation", "")
        if operation not in VALID_OPERATIONS:
            raise ValueError(
                f"Invalid operation: '{operation}'. Must be one of: {', '.join(sorted(VALID_OPERATIONS))}"
            )
        handler = HANDLERS[operation]
        result = handler(params)
        resp = {"id": req.get("id"), "result": json.dumps(result, indent=2)}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
