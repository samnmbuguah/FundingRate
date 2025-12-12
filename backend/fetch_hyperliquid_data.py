import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app import app, fetch_and_store_hyperliquid_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_hyperliquid_data_cron")

if __name__ == "__main__":
    logger.info("Starting scheduled Hyperliquid data fetch...")
    try:
        with app.app_context():
            fetch_and_store_hyperliquid_data()
        logger.info("Hyperliquid data fetch completed successfully.")
    except Exception as e:
        logger.error(f"Error in scheduled Hyperliquid data fetch: {e}")
        sys.exit(1)
