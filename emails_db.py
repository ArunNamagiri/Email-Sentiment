import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from datetime import datetime, timezone
import logging
from psycopg2 import sql 

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
log = logging.getLogger('emails_db')

def get_connection():
    """Establishes a connection to the PostgreSQL database."""
    DATABASE_URL = os.environ.get("DATABASE_URL") 
    
    if not DATABASE_URL:
        log.error("FATAL ERROR: DATABASE_URL environment variable is not set.")
        return None 
    
    try:
        result = urlparse(DATABASE_URL)
        
        query_params = dict(item.split('=') for item in result.query.split('&') if '=' in item) if result.query else {}
        ssl_mode = query_params.get('sslmode', 'require') 

        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            sslmode=ssl_mode,
            cursor_factory=RealDictCursor 
        )
        return conn
    except Exception as e:
        log.error(f"Failed to connect to database. Please check DATABASE_URL and firewall settings. Error: {e}", exc_info=True)
        return None

def recreate_table():
    """Drops and recreates the emails table."""
    conn = get_connection()
    if conn is None: 
        log.error("❌ Cannot recreate table: Database connection failed.")
        return

    try:
        cur = conn.cursor()
        
        cur.execute("DROP TABLE IF EXISTS emails CASCADE;")
        
        cur.execute("""
            CREATE TABLE emails (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                subject TEXT,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                body TEXT,
                ai_sentiment TEXT,
                rule_sentiment TEXT,
                summary TEXT,
                suggested_reply TEXT,
                forwarded_to TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        log.info("'emails' table recreated successfully.")
    except Exception as e:
        log.error(f"Error recreating table: {e}", exc_info=True)
        conn.rollback()
    finally:
        if conn:
            conn.close()

def insert_email(sender: str, subject: str, timestamp: datetime, body: str, 
                   ai_sentiment: str, rule_sentiment: str, summary: str, suggested_reply: str, forwarded_to: str):
    """Inserts a new analyzed email record into the database."""
    conn = get_connection()
    if conn is None: return None

    try:
        cur = conn.cursor()
        
        insert_query = sql.SQL("""
            INSERT INTO emails (sender, subject, timestamp, body, ai_sentiment, rule_sentiment, summary, suggested_reply, forwarded_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """)
        
        ts_utc = timestamp.astimezone(timezone.utc)
        
        cur.execute(insert_query, (
            sender, 
            subject, 
            ts_utc, 
            body, 
            ai_sentiment, 
            rule_sentiment, 
            summary, 
            suggested_reply,
            forwarded_to
        ))
        
        email_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        return email_id
    except Exception as e:
        log.error(f"Error inserting email: {e}", exc_info=True)
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def get_all_emails(limit: int = 10):
    """Fetches emails from the database, newest first, with an optional limit."""
    conn = get_connection()
    if conn is None: return []

    try:
        cur = conn.cursor()
        
        query = sql.SQL("SELECT * FROM emails ORDER BY timestamp DESC LIMIT %s;")
            
        cur.execute(query, (limit,))
        emails = cur.fetchall()
        cur.close()
        return emails
    except Exception as e:
        log.error(f"Error fetching all emails: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()

def get_stats():
    """Calculates sentiment statistics for the dashboard."""
    conn = get_connection()
    if conn is None:
        return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) as total FROM emails;")
        total = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as count FROM emails WHERE ai_sentiment='Positive';")
        positive = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM emails WHERE ai_sentiment='Negative';")
        negative = cur.fetchone()['count']
        
        neutral = total - (positive + negative) 
        
        return {'total': total, 'positive': positive, 'negative': negative, 'neutral': neutral}
    except Exception as e:
        log.error(f"Error calculating stats: {e}", exc_info=True)
        return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
    finally:
        if conn:
            conn.close()

def get_sentiment_counts_for_graph():
    """Returns sentiment counts in a format suitable for the chart."""
    stats = get_stats()
    return {
        'Positive': stats['positive'],
        'Negative': stats['negative'],
        'Neutral': stats['neutral']
    }

def test_db_connection():
    """Tests if a connection to the database can be established."""
    conn = get_connection()
    if conn:
        conn.close()
        log.info("Database connection test successful.")
        return True
    log.error("Database connection test failed.")
    return False
