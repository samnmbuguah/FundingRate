from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from lighter_client import LighterClient
from models import db, FundingRate
from datetime import datetime, timedelta

import logging
import os

# Configure logging
log_file_path = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Determine if we're in production
# Check if running under Passenger (cPanel deployment)
IS_PRODUCTION = os.environ.get('PASSENGER_BASE_URI') is not None or os.environ.get('FLASK_ENV') == 'production'

# Note: In production with Passenger, static files are served from the public/ directory
# Passenger handles this automatically, so we don't configure Flask's static folder
app = Flask(__name__)

CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///funding_rates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

client = LighterClient()

def fetch_and_store_data():
    """
    Scheduled job to fetch data from Lighter API and store in database.
    """
    logger.info("Fetching and storing funding rate data...")
    try:
        # Fetch current rates from API
        response = client.session.get(f"{client.BASE_URL}/funding-rates")
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        items = data.get('funding_rates', []) if isinstance(data, dict) else data
        
        with app.app_context():
            for item in items:
                symbol = item.get('symbol')
                rate_str = item.get('rate', '0')
                try:
                    rate = float(rate_str)
                except ValueError:
                    rate = 0.0
                
                # Store in database
                funding_rate = FundingRate(symbol=symbol, rate=rate)
                db.session.add(funding_rate)
            
            db.session.commit()
            logger.info(f"Stored {len(items)} funding rates in database.")
    except Exception as e:
        logger.error(f"Failed to fetch/store data: {e}")

# Scheduler removed in favor of system cron job to prevent multiple workers issue
# See backend/fetch_data.py

# Create tables and initial fetch
with app.app_context():
    db.create_all()
    fetch_and_store_data()

@app.route('/api/funding_rates', methods=['GET'])
def get_funding_rates():
    """
    Calculate 2-day average funding rates from database and return top opportunities.
    """
    try:
        # Get data from last 48 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        
        # Query all records from last 48 hours
        recent_rates = FundingRate.query.filter(FundingRate.timestamp >= cutoff_time).all()
        
        if not recent_rates:
            logger.warning("No data in database for last 48 hours.")
            return jsonify({
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            })
        
        # Group by symbol and calculate average
        symbol_rates = {}
        for record in recent_rates:
            if record.symbol not in symbol_rates:
                symbol_rates[record.symbol] = []
            symbol_rates[record.symbol].append(record.rate)
        
        # Calculate averages
        averages = []
        for symbol, rates in symbol_rates.items():
            avg_rate = sum(rates) / len(rates)
            averages.append({
                "symbol": symbol,
                "average_2day_rate": avg_rate
            })
        
        # Sort for top opportunities
        # Top Long: Most negative rates (shorts pay longs)
        top_long = sorted(averages, key=lambda x: x['average_2day_rate'])
        
        # Top Short: Most positive rates (longs pay shorts)
        top_short = sorted(averages, key=lambda x: x['average_2day_rate'], reverse=True)
        
        # Calculate next funding time (assuming hourly funding)
        now = datetime.utcnow()
        next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        return jsonify({
            "top_long": top_long,
            "top_short": top_short,
            "timestamp": now.isoformat() + 'Z',
            "next_funding_time": next_funding.isoformat() + 'Z'
        })
    except Exception as e:
        logger.error(f"Error calculating funding rates: {e}")
        return jsonify({
            "top_long": [],
            "top_short": [],
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "next_funding_time": None
        }), 500

@app.route('/api/funding_rates/<symbol>', methods=['GET'])
def get_symbol_history(symbol):
    """
    Get historical funding rates for a specific symbol.
    """
    try:
        # Get data from last 7 days for charts
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        # Ensure symbol is uppercase
        symbol = symbol.upper()
        
        history = FundingRate.query.filter(
            FundingRate.symbol == symbol,
            FundingRate.timestamp >= cutoff_time
        ).order_by(FundingRate.timestamp.asc()).all()
        
        if not history:
            logger.warning(f"No history found for symbol: {symbol}")
        
        return jsonify([item.to_dict() for item in history])
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return jsonify([]), 500

# Serve frontend - Passenger serves static files from public/, but we need to handle SPA routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """
    Serve the frontend application.
    Static files in public/ are served directly by Passenger.
    This route handles SPA routing by serving index.html for non-static requests.
    """
    # API routes are handled above, this catches everything else
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    
    # For the root or any SPA route, serve index.html
    # Passenger will serve the actual file from public/index.html
    public_dir = os.path.join(os.path.dirname(__file__), '..', 'public')
    
    # If it's a static file request (has extension and exists), serve it
    if path and '.' in path.split('/')[-1]:
        file_path = os.path.join(public_dir, path)
        if os.path.exists(file_path):
            return send_from_directory(public_dir, path)
    
    # Otherwise serve index.html for SPA routing
    return send_from_directory(public_dir, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=not IS_PRODUCTION)
