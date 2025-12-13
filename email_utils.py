import imaplib
import email
from email.header import decode_header
import logging
from dotenv import load_dotenv
import os
import re
from html.parser import HTMLParser

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
log = logging.getLogger('email_utils')

load_dotenv("secretkeys.env")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)

def strip_html(html: str) -> str:
    """Strips all HTML tags from a string."""
    s = HTMLStripper()
    try:
        s.feed(html)
        stripped = re.sub(r'\s*\n\s*', '\n', s.get_data())
        return re.sub(r' {2,}', ' ', stripped).strip()
    except Exception as e:
        log.error(f"Error during HTML stripping: {e}")
        return html 

def get_email_body(msg: email.message.Message) -> str:
    """Extracts the plain text body from a message object, prioritizing text over HTML."""
    body_text = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = part.get_content_disposition()
            
            if cdisp in ['attachment', 'inline'] and ctype not in ['text/plain', 'text/html']:
                continue

            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                
                charset = part.get_content_charset() or 'utf-8'
                decoded_payload = payload.decode(charset, errors='ignore')

                if ctype == 'text/plain':
                    body_text = decoded_payload
                    break 
                elif ctype == 'text/html':
                    body_html = decoded_payload
            except Exception as e:
                log.error(f"Error decoding email part: {e}")
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload is not None:
                body_text = payload.decode('utf-8', errors='ignore')
            else:
                body_text = str(msg.get_payload() or "")
        except Exception as e:
            log.error(f"Error processing non-multipart message: {e}")
            body_text = ""
    
    if body_text.strip():
        return body_text.strip()

    if body_html.strip():
        return strip_html(body_html).strip()
        
    return ""

def clean_email_body(body: str) -> str:
    """Removes common email reply/forward headers and excessive whitespace."""
    if not body:
        return ""
    
    cleaned_body = re.split(r'On\s+.*wrote:|Message\-ID:.*|<.*@.*>.*Sent:.*|-----Original Message-----|\s*From:.*Sent:.*To:.*Subject:', body, 1, re.IGNORECASE)[0]
    
    lines = cleaned_body.split('\n')
    cleaned_lines = [line for line in lines if not line.strip().startswith('>')]
    cleaned_body = '\n'.join(cleaned_lines)
    
    cleaned_body = re.sub(r'(\n[ \t]*){3,}', '\n\n', cleaned_body).strip()
    
    return cleaned_body
