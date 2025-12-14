import os
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv("secretkeys.env")

log = logging.getLogger("emails_db")
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Create and return a PostgreSQL connection using DictCursor."""
    if not DATABASE_URL:
        log.critical("❌ DATABASE_URL is not set in environment variables")
        return None

    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        log.critical(f"❌ Database connection failed: {e}", exc_info=True)
        return None

def create_emails_table():
    """Create emails table if it does not exist."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id SERIAL PRIMARY KEY,
                    sender VARCHAR(255) NOT NULL,
                    subject VARCHAR(255),
                    timestamp TIMESTAMPTZ,
                    body TEXT,
                    ai_sentiment VARCHAR(50),
                    rule_sentiment VARCHAR(50),
                    summary TEXT,
                    suggested_reply TEXT,
                    forwarded_to_team VARCHAR(255)
                );
            """)
            conn.commit()
            log.info("✅ Emails table ready")
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Error creating table: {e}", exc_info=True)
    finally:
        conn.close()


def insert_email(
    sender,
    subject,
    timestamp,
    body,
    ai_sentiment,
    rule_sentiment,
    summary,
    suggested_reply,
    forwarded_to_team
):
    """Insert one analyzed email into DB."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emails (
                    sender, subject, timestamp, body,
                    ai_sentiment, rule_sentiment,
                    summary, suggested_reply, forwarded_to_team
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                sender,
                subject,
                timestamp,
                body,
                ai_sentiment,
                rule_sentiment,
                summary,
                suggested_reply,
                forwarded_to_team
            ))
            conn.commit()
            log.info(f"✅ Stored email from {sender}")
            return True
    except Exception as e:
        conn.rollback()
        log.error(f"❌ Email insert failed: {e}", exc_info=True)
        return False
    finally:
        conn.close()

def get_all_emails(limit=1000):
    """Fetch latest emails for dashboard."""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id, sender, subject, timestamp, body,
                    ai_sentiment, rule_sentiment,
                    summary, suggested_reply, forwarded_to_team
                FROM emails
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    except Exception as e:
        log.error(f"❌ Error fetching emails: {e}", exc_info=True)
        return []
    finally:
        conn.close()

def get_stats():
    """Return sentiment statistics."""
    conn = get_db_connection()
    if conn is None:
        return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM emails")
            total = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS count FROM emails WHERE ai_sentiment='Positive'")
            positive = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) AS count FROM emails WHERE ai_sentiment='Negative'")
            negative = cur.fetchone()["count"]

            neutral = total - (positive + negative)

            return {
                'total': total,
                'positive': positive,
                'negative': negative,
                'neutral': neutral
            }
    except Exception as e:
        log.error(f" Stats calculation failed: {e}", exc_info=True)
        return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
    finally:
        conn.close()


def get_sentiment_counts_for_graph():
    stats = get_stats()
    return {
        "Positive": stats["positive"],
        "Negative": stats["negative"],
        "Neutral": stats["neutral"]
    }


def test_db_connection():
    conn = get_db_connection()
    if conn:
        conn.close()
        log.info(" Database connection successful")
        return True
    log.error(" Database connection failed")
    return False
