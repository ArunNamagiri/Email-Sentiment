from gmail_auth import authenticate_gmail
from email_utils import parse_email
from ollama_utils import analyze_sentiment
from db_utils import save_email_to_db

def assign_team(sentiment):
    if sentiment == "positive":
        return "Feedback"
    elif sentiment == "negative":
        return "Support"
    return "Operations"

def fetch_and_store_emails():
    service = authenticate_gmail()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])

    if not messages:
        print("📭 No new unread messages.")
        return

    for msg in messages:
        msg_id = msg['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        parsed = parse_email(msg_data)
        if not parsed:
            continue

        print(f"📥 Processing email from: {parsed['sender']}")

        sentiment, score = analyze_sentiment(parsed['body'])
        team = assign_team(sentiment)

        save_email_to_db(parsed['sender'], parsed['subject'], parsed['body'], sentiment, score, team)

        # Mark as read
        service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
