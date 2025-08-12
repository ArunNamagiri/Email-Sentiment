import base64

def parse_email(msg_data):
    try:
        payload = msg_data['payload']
        headers = payload['headers']
        parts = payload.get('parts', [])
        body = ""

        for part in parts:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode()
                break

        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

        return {
            'sender': sender,
            'subject': subject,
            'body': body.strip()
        }

    except Exception as e:
        print(f"Failed to parse email: {e}")
        return None
