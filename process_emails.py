import os
import imaplib
import email
from email.header import decode_header, make_header
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from emails_db import insert_email
from email_utils import get_email_body, clean_email_body
from llm_analyzer import llm_analyze_email 
from email_sender import forward_email_by_sentiment, get_recipient_email 

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv("secretkeys.env")


GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


def rule_based_sentiment(body: str) -> str:
    """Simple rule-based analysis for quick classification."""
    body = body.lower()
    if any(w in body for w in ["urgent", "immediately", "critical", "escalate"]):
        return "Negative"
    if any(w in body for w in ["great", "thanks", "excellent", "happy"]):
        return "Positive"
    return "Neutral"


def has_unread_emails() -> bool:
    """Checks if there are any unread emails in the inbox."""
    if not (GMAIL_USER and GMAIL_PASS):
        log.error("GMAIL credentials missing. Set GMAIL_USER and GMAIL_PASS.")
        return False
        
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        
        status, email_ids = mail.search(None, "UNSEEN")
        mail.logout()
        
        return status == "OK" and bool(email_ids and email_ids[0].strip())
        
    except Exception as e:
        log.error(f"Error checking for unread emails: {e}", exc_info=True)
        return False

def process_unread_emails(limit: int = 5) -> int:
    """Fetches, analyzes, forwards, and marks unread emails as seen."""
    if not (GMAIL_USER and GMAIL_PASS):
        log.error("GMAIL credentials missing. Cannot process emails.")
        return 0

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(GMAIL_USER, GMAIL_PASS)
    mail.select("inbox")

    status, email_ids = mail.search(None, "UNSEEN")
    if status != "OK" or not email_ids or not email_ids[0].strip():
        log.info("No unread emails found.")
        mail.logout()
        return 0

    ids = email_ids[0].split()[-limit:]
    count = 0

    for eid in ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        sender = str(make_header(decode_header(msg.get("From", ""))))
        subject = str(make_header(decode_header(msg.get("Subject", ""))))

        raw_body = get_email_body(msg)
        cleaned_body = clean_email_body(raw_body) 

        rule_sent = rule_based_sentiment(raw_body)
        ai = llm_analyze_email(cleaned_body, subject)

        date_tuple = email.utils.parsedate_tz(msg.get("Date"))
        timestamp = (
            datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if date_tuple else datetime.now(timezone.utc)
        )

        # --- DETERMINE RECIPIENT ---
        forward_team = get_recipient_email(ai.get("sentiment"))
        
        # 1. Store in DB
        insert_email(
            sender=sender,
            subject=subject,
            timestamp=timestamp,
            body=raw_body,
            ai_sentiment=ai.get("sentiment"),
            rule_sentiment=rule_sent,
            summary=ai.get("summary"),
            suggested_reply=ai.get("suggested_reply"),
            forwarded_to_team=forward_team
        )
        
        # 2. Forward the email (CRITICAL FIX: Pass recipient_email)
        forward_email_by_sentiment(
            recipient_email=forward_team,  # <--- NEW ARGUMENT
            sender=sender,
            subject=subject,
            original_body=raw_body,
            ai_sentiment=ai.get("sentiment"),
            ai_summary=ai.get("summary", ""),
            ai_reply=ai.get("suggested_reply", ""),
        )
        
        # 3. Mark email as SEEN
        mail.store(eid, '+FLAGS', '\\Seen')
        count += 1
        log.info(f"Processed email from {sender} with subject: {subject[:30]}...")

    mail.logout()
    return count