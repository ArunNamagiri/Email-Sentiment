import os
import time
import logging
from dotenv import load_dotenv

from emails_db import test_db_connection
from process_emails import process_unread_emails

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
log = logging.getLogger('fetch_loop')

load_dotenv("secretkeys.env", override=True)

try:
    FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", 60)) 
except ValueError:
    FETCH_INTERVAL_SECONDS = 60 
    log.warning("FETCH_INTERVAL_SECONDS in .env is not an integer. Defaulting to 60s.")


def main_loop():
    log.info(f"--- Starting Email Fetch Loop (Interval: {FETCH_INTERVAL_SECONDS}s) ---")

    if not test_db_connection():
        log.error(" Exiting due to DB connection failure.")
        return
        
    
    while True:
        try:
            # Fetches up to 5 emails in each loop
            count = process_unread_emails(limit=5) 
            
            if count > 0:
                log.info(f"Processed {count} new unread emails.")
            else:
                log.info("No new unread emails found.")

        except Exception as e:
            log.error(f"Critical error in fetch loop: {e}", exc_info=True)
            # Sleep longer on critical errors to prevent rapid failure loop
            time.sleep(FETCH_INTERVAL_SECONDS * 5) 
            
        time.sleep(FETCH_INTERVAL_SECONDS)

    log.info("--- Email Fetch Loop Ended ---")


if __name__ == "__main__":
    main_loop()