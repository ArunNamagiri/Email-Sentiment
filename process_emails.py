import os
import imaplib
import email
from email.header import decode_header, make_header
import requests
import logging
import json
import time
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from emails_db import get_connection, insert_email 
from email_utils import get_email_body, clean_email_body
import smtplib
from email.message import EmailMessage


logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(root)s: %(message)s')
log = logging.getLogger('root')


load_dotenv("secretkeys.env")

LLM_API_URL = os.environ.get("LLM_API_URL") 
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", 'llama3') 

DB_URL = os.environ.get("DATABASE_URL")

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
MAX_RETRIES = 3
INITIAL_DELAY_SECONDS = 2
REQUEST_TIMEOUT = 30 


if not DB_URL:
    log.error("DATABASE_URL environment variable is not set.")
if not LLM_API_URL or not LLM_API_KEY:
    log.error("LLM_API_URL or LLM_API_KEY environment variables are not set. LLM analysis will fail.")
if not GMAIL_USER or not GMAIL_PASS:
    log.error("GMAIL_USER or GMAIL_PASS environment variables are not set.")


def rule_based_sentiment(body: str) -> str:
    """Simple rule-based analysis for extreme cases."""
    body = body.lower()
    if any(word in body for word in ["urgent", "immediately", "critical", "escalate"]):
        return "Negative"
    if any(word in body for word in ["great", "thanks", "excellent", "happy"]):
        return "Positive"
    return "Neutral"

def llm_analyze_email(body: str, subject: str) -> dict:
    """Calls the hosted LLM API to analyze email and return structured JSON."""
    if not LLM_API_URL or not LLM_API_KEY:
        log.warning("LLM API credentials missing. Skipping AI analysis.")
        return {"sentiment": "LLM_Skipped", "summary": "API config missing.", "suggested_reply": "LLM Analysis skipped."}

    system_prompt = (
        "You are an expert email analysis and summarization assistant. "
        "Your task is to analyze the provided email's subject and body and "
        "return a single JSON object with the following three keys: "
        "'sentiment' (one word: 'Positive', 'Negative', or 'Neutral'), "
        "'summary' (a concise 1-2 sentence summary of the email's core content and request), and "
        "'suggested_reply' (a short, professional, and helpful reply draft). "
        "Do not include any text outside the JSON object. "
        "Ensure the response is valid, clean JSON."
    )

    user_query = f"Email Subject: {subject}\n\nEmail Body:\n{body}"
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "sentiment": {"type": "STRING", "description": "One word: Positive, Negative, or Neutral."},
            "summary": {"type": "STRING", "description": "A concise 1-2 sentence summary of the email's core content and request."},
            "suggested_reply": {"type": "STRING", "description": "A short, professional, and helpful reply draft."}
        },
        "required": ["sentiment", "summary", "suggested_reply"]
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": user_query}
                ]
            }
        ],
        
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },

        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }
   
    final_api_url = f"{LLM_API_URL}?key={LLM_API_KEY}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                final_api_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                },
                timeout=REQUEST_TIMEOUT 
            )
            response.raise_for_status() 
            api_response_data = response.json()
            
            result_content = api_response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

            if result_content.startswith("```json") and result_content.endswith("```"):
                json_string = result_content[7:-3].strip()
            else:
                json_string = result_content.strip()
                
            ai_analysis = json.loads(json_string)

            if all(key in ai_analysis for key in ['sentiment', 'summary', 'suggested_reply']):
                return {
                    "sentiment": ai_analysis['sentiment'].strip().title(),
                    "summary": ai_analysis['summary'].strip(),
                    "suggested_reply": ai_analysis['suggested_reply'].strip()
                }
            else:
                log.error(f"LLM returned incomplete JSON keys: {ai_analysis}")
                return {"sentiment": "LLM_Failed", "summary": "Incomplete LLM output.", "suggested_reply": "Error: Incomplete analysis."}

        except requests.exceptions.HTTPError as e:
            log.error(f"LLM API HTTP Error on attempt {attempt + 1}: {e} - Response: {response.text}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(INITIAL_DELAY_SECONDS * (2 ** attempt))
            else:
                return {"sentiment": "LLM_Failed", "summary": "LLM API failed.", "suggested_reply": "Error: LLM API failed."}
        except requests.exceptions.RequestException as e:
            log.error(f"LLM API Connection Error on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(INITIAL_DELAY_SECONDS * (2 ** attempt))
            else:
                return {"sentiment": "LLM_Failed", "summary": "LLM connection failed.", "suggested_reply": "Error: LLM connection failed."}
        except json.JSONDecodeError:
            log.error(f"LLM returned invalid JSON on attempt {attempt + 1}: {result_content}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(INITIAL_DELAY_SECONDS * (2 ** attempt))
            else:
                return {"sentiment": "LLM_Failed", "summary": "LLM returned invalid JSON.", "suggested_reply": "Error: Invalid analysis format."}

    return {"sentiment": "LLM_Failed", "summary": "LLM process failed after retries.", "suggested_reply": "Error: Processing timed out."}


def gmail_auth(user: str, password: str, server: str, port: int) -> imaplib.IMAP4_SSL:
    """Connects and logs into the Gmail IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(user, password)
        return mail
    except Exception as e:
        log.error(f"IMAP login failed: {e}")
        raise

def process_unread_emails(limit: int = 5) -> int:
    """Connects, fetches, analyzes, and inserts unread emails."""
    
    if not all([DB_URL, LLM_API_URL, GMAIL_USER, GMAIL_PASS]):
        log.error("Missing critical environment variables (DB, LLM, or Gmail). Aborting email processing.")
        return 0
    
    mail = None
    count = 0
    
    try:
        mail = gmail_auth(GMAIL_USER, GMAIL_PASS, IMAP_SERVER, IMAP_PORT)
        mail.select('inbox')
        
        status, email_ids = mail.search(None, 'UNSEEN')
        if status != 'OK':
            log.info("No unread emails found or search failed.")
            return 0

        email_id_list = email_ids[0].split()
        latest_ids = email_id_list[-limit:] 

        for eid in latest_ids:
            try:
                status, msg_data = mail.fetch(eid, '(RFC822)')
                if status != 'OK':
                    log.error(f"Failed to fetch email ID {eid}")
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                
   
                sender_decoded = decode_header(msg['From'])
                sender = str(make_header(sender_decoded))

                
                subject_decoded = decode_header(msg['Subject'])
                subject = str(make_header(subject_decoded))
                
                raw_body = get_email_body(msg)
                
                rule_sentiment = rule_based_sentiment(raw_body)
                
                cleaned_body = clean_email_body(raw_body)
                
                ai_result = llm_analyze_email(cleaned_body, subject)


                final_sentiment = ai_result.get("sentiment", "Neutral")

                if final_sentiment not in ["Positive", "Negative", "Neutral"]:
                     final_sentiment = "Neutral"

                forwarded_to = forward_email(
                     original_sender=sender,
                    subject=subject,
                    body=cleaned_body,
                    sentiment=final_sentiment
                )
                
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    local_dt = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    timestamp_utc = local_dt.astimezone(timezone.utc)
                else:
                    timestamp_utc = datetime.now(timezone.utc) 

                insert_email(
                    sender=sender, 
                    subject=subject, 
                    timestamp=timestamp_utc, 
                    body=raw_body,
                    ai_sentiment=ai_result.get('sentiment'), 
                    rule_sentiment=rule_sentiment,
                    summary=ai_result.get('summary'),
                    suggested_reply=ai_result.get('suggested_reply'),
                    forwarded_to=forwarded_to

                )
                
                mail.store(eid, '+FLAGS', '\\Seen')
                
                log.info(f"Email from '{sender}' (Subject: {subject[:30]}...) processed. Sentiment: {ai_result.get('sentiment')}\n")
                count += 1

            except Exception as e:
                log.error(f"Error processing individual email ID {eid}: {e}", exc_info=True)
                
        return count

    except Exception as e:
        log.error(f"Critical error during batch processing: {e}", exc_info=True)
        raise e
        
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass
        log.info(f"Processed {count} emails in this batch.")

   
def forward_email(original_sender, subject, body, sentiment):
    team_map = {
        "Positive": os.getenv("POSITIVE_TEAM_EMAIL"),
        "Negative": os.getenv("NEGATIVE_TEAM_EMAIL"),
        "Neutral": os.getenv("NEUTRAL_TEAM_EMAIL"),
    }

    to_email = team_map.get(sentiment, team_map["Neutral"])

    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = f"[{sentiment}] {subject}"

    msg.set_content(f"""
Forwarded Email

From: {original_sender}
Sentiment: {sentiment}

------------------
{body}
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
            log.info(f"Forwarded to {to_email}")
    except Exception as e:
        log.error(f"Forward failed: {e}", exc_info=True)

    return to_email
