import sys
import os
import logging

# Add the parent directory to sys.path to allow imports from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import app, fetch_and_store_data

# Configure logging for the script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_data_cron")

if __name__ == "__main__":
    logger.info("Starting scheduled data fetch...")
    try:
        with app.app_context():
            fetch_and_store_data()
        logger.info("Data fetch completed successfully.")
    except Exception as e:
        logger.error(f"Error in scheduled data fetch: {e}")
        sys.exit(1)
