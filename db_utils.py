import sqlite3

def save_email_to_db(sender, subject, body, sentiment=None, score=None, team=None):
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emails (sender, subject, body, sentiment, score, team)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sender, subject, body, sentiment, score, team))
    conn.commit()
    conn.close()

def get_all_emails():
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, subject, body, sentiment, team FROM emails")
    rows = cursor.fetchall()
    conn.close()
    return [
        {'id': r[0], 'sender': r[1], 'subject': r[2], 'body': r[3], 'sentiment': r[4], 'team': r[5]}
        for r in rows
    ]

def get_sentiment_summary():
    conn = sqlite3.connect("emails.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sentiment, COUNT(*) FROM emails GROUP BY sentiment")
    result = cursor.fetchall()
    conn.close()
    summary = {'positive': 0, 'negative': 0, 'neutral': 0}
    for sentiment, count in result:
        summary[sentiment] = count
    return summary
