from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from lighter_client import LighterClient
from models import db, FundingRate
from datetime import datetime, timedelta
import atexit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Schedule the job - every 1 minute
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_and_store_data, trigger="interval", minutes=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

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
                "timestamp": datetime.utcnow().isoformat()
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
        top_long = sorted(averages, key=lambda x: x['average_2day_rate'])[:10]
        
        # Top Short: Most positive rates (longs pay shorts)
        top_short = sorted(averages, key=lambda x: x['average_2day_rate'], reverse=True)[:10]
        
        return jsonify({
            "top_long": top_long,
            "top_short": top_short,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error calculating funding rates: {e}")
        return jsonify({
            "top_long": [],
            "top_short": [],
            "timestamp": datetime.utcnow().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
