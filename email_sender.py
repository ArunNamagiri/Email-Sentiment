# email_sender.py (Ensure this is the structure of your file)
import logging
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv("secretkeys.env")

# Global variables loaded from environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("GMAIL_USER")
SENDER_PASS = os.getenv("GMAIL_PASS") # App-specific password if using Gmail

# --- Helper Functions ---

def get_recipient_email(sentiment: str) -> str:
    """Returns the team email address based on sentiment."""
    if sentiment == "Negative":
        return os.getenv("NEGATIVE_TEAM_EMAIL")
    elif sentiment == "Positive":
        return os.getenv("POSITIVE_TEAM_EMAIL")
    else:
        return os.getenv("NEUTRAL_TEAM_EMAIL")


def forward_email_by_sentiment(
    recipient_email: str, 
    sender: str, 
    subject: str, 
    original_body: str, 
    ai_sentiment: str, 
    ai_summary: str, 
    ai_reply: str
):
    """
    Constructs a new email containing the analysis and forwards it 
    to the designated recipient team.
    """
    if not (SENDER_EMAIL and SENDER_PASS):
        logging.error("SMTP credentials missing. Cannot send email.")
        return

    msg = EmailMessage()
    msg['Subject'] = f"[SENTIMENT: {ai_sentiment.upper()}] FW: {subject}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    body_html = f"""
    <html>
        <body>
            <h2>AI Sentiment Analysis</h2>
            <p><strong>Original Sender:</strong> {sender}</p>
            <p><strong>Analyzed Sentiment:</strong> <strong>{ai_sentiment}</strong></p>
            <p><strong>Summary:</strong> {ai_summary}</p>
            <hr>
            <h3>Suggested Reply Draft</h3>
            <pre style="background-color: #f4f4f4; padding: 10px; border-radius: 5px;">{ai_reply}</pre>
            <hr>
            <h3>Original Email Body</h3>
            <blockquote style="border-left: 3px solid #ccc; margin: 1em 0; padding: 0.5em 10px;">{original_body}</blockquote>
        </body>
    </html>
    """
    msg.set_content(body_html, subtype='html')

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.send_message(msg)
        logging.info(f"Email forwarded successfully to {recipient_email} for sentiment: {ai_sentiment}")
    except Exception as e:
        logging.error(f"Failed to forward email to {recipient_email}: {e}")