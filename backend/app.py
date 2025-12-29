from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

try:
    # When imported as part of the backend package (production / Passenger)
    from .lighter_client import LighterClient
    from .hyena_client import HyenaClient
    from .models import db, FundingRate
except ImportError:
    # When running app.py directly (local development)
    from lighter_client import LighterClient
    from hyena_client import HyenaClient
    from models import db, FundingRate
from datetime import datetime, timedelta
import json

import logging
import os
import math

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
app = Flask(__name__, instance_relative_config=True)

CORS(app, origins=['http://maxquant.online', 'https://maxquant.online', 'http://localhost:5173', 'http://localhost:5000'])


# Initialize database
INSTANCE_DIR = app.instance_path
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, 'funding_rates.db')
db_uri = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or ('sqlite:///' + DB_PATH)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

client = LighterClient()
hyena_client = HyenaClient()

def _status_file_path() -> str:
    return os.path.join(INSTANCE_DIR, 'status.json')

def _write_status(data: dict) -> None:
    try:
        with open(_status_file_path(), 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to write status: {e}")

def _read_status() -> dict:
    try:
        with open(_status_file_path(), 'r') as f:
            return json.load(f)
    except Exception:
        return {"status": "idle"}

def _lock_path(job: str) -> str:
    return os.path.join(INSTANCE_DIR, f"{job}.lock")

def _acquire_lock(job: str) -> bool:
    path = _lock_path(job)
    try:
        # Atomic create; fail if exists
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(f"pid={os.getpid()} started={datetime.utcnow().isoformat()}Z\n")
        return True
    except FileExistsError:
        # Check if lock is stale
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
            
            # Extract timestamp
            # Format: pid=123 started=2024-01-01T00:00:00.000000Z
            import re
            match = re.search(r'started=([\d\-T:\.Z]+)', content)
            if match:
                started_str = match.group(1).rstrip('Z')
                # Truncate microseconds if present to match format expected by fromisoformat
                if '.' in started_str:
                     started_str = started_str[:26] 
                
                started_at = datetime.fromisoformat(started_str)
                age = datetime.utcnow() - started_at
                
                if age > timedelta(minutes=30):
                    logger.warning(f"Found stale lock for '{job}' (age: {age}). Removing...")
                    os.remove(path)
                    # Try converting to recursion or just retry once
                    return _acquire_lock(job)
        except Exception as e:
            logger.error(f"Error checking stale lock for '{job}': {e}")

        logger.warning(f"Job '{job}' already running; skipping new invocation.")
        return False
    except Exception as e:
        logger.error(f"Failed to acquire lock for '{job}': {e}")
        return False

def _release_lock(job: str) -> None:
    path = _lock_path(job)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"Failed to release lock for '{job}': {e}")

def fetch_and_store_data():
    """
    Scheduled job to fetch data from Lighter API and store in database.
    """
    logger.info("Fetching and storing funding rate data (lighter)...")
    if not _acquire_lock('lighter'):
        return
    try:
        _write_status({
            "job": "lighter",
            "status": "running",
            "started_at": datetime.utcnow().isoformat() + 'Z'
        })
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
                except (TypeError, ValueError):
                    # Skip completely invalid rates
                    logger.warning(f"Skipping invalid rate for symbol {symbol}: {rate_str}")
                    continue

                # Filter out NaN/inf values which break downstream calculations
                if not math.isfinite(rate):
                    logger.warning(f"Skipping non-finite rate for symbol {symbol}: {rate}")
                    continue
                
                # Store in database
                funding_rate = FundingRate(exchange='lighter', symbol=symbol, rate=rate)
                db.session.add(funding_rate)
            
            db.session.commit()
            logger.info(f"Stored {len(items)} lighter funding rates in database.")
            _write_status({
                "job": "lighter",
                "status": "completed",
                "stored": len(items),
                "completed_at": datetime.utcnow().isoformat() + 'Z'
            })
    except Exception as e:
        logger.error(f"Failed to fetch/store lighter data: {e}")
        _write_status({
            "job": "lighter",
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat() + 'Z'
        })
    finally:
        _release_lock('lighter')


def fetch_and_store_hyperliquid_data():
    """
    Scheduled job to fetch data from Hyperliquid (via HyenaClient) and store in database.
    """
    logger.info("Fetching and storing Hyperliquid funding rate data...")
    if not _acquire_lock('hyperliquid'):
        return
    try:
        _write_status({
            "job": "hyperliquid",
            "status": "running",
            "started_at": datetime.utcnow().isoformat() + 'Z'
        })
        # Use the slower method that fetches ALL markets
        payload = hyena_client.fetch_all_funding_rates()

        items = []
        if isinstance(payload, dict):
            items.extend(payload.get("top_long", []))
            items.extend(payload.get("top_short", []))

        symbol_rates = {}
        for item in items:
            symbol = item.get("symbol")
            rate_value = item.get("average_3day_rate")

            if symbol is None or rate_value is None:
                continue

            try:
                rate = float(rate_value)
            except (TypeError, ValueError):
                logger.warning(f"Skipping invalid Hyperliquid rate for symbol {symbol}: {rate_value}")
                continue

            if not math.isfinite(rate):
                logger.warning(f"Skipping non-finite Hyperliquid rate for symbol {symbol}: {rate}")
                continue

            symbol_rates[symbol] = rate

        if not symbol_rates:
            logger.warning("No usable Hyperliquid funding data to store.")
            return

        with app.app_context():
            for symbol, rate in symbol_rates.items():
                funding_rate = FundingRate(exchange='hyperliquid', symbol=symbol, rate=rate)
                db.session.add(funding_rate)

            db.session.commit()
            logger.info(f"Stored {len(symbol_rates)} Hyperliquid funding rates in database.")
            _write_status({
                "job": "hyperliquid",
                "status": "completed",
                "stored": len(symbol_rates),
                "completed_at": datetime.utcnow().isoformat() + 'Z'
            })
    except Exception as e:
        logger.error(f"Failed to fetch/store Hyperliquid data: {e}")
        _write_status({
            "job": "hyperliquid",
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat() + 'Z'
        })
    finally:
        _release_lock('hyperliquid')

# Scheduler removed in favor of system cron job to prevent multiple workers issue
# See backend/fetch_data.py

# Create tables and initial fetch
try:
    with app.app_context():
        db.create_all()
        fetch_and_store_data()
        fetch_and_store_hyperliquid_data()
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        return jsonify(_read_status())
    except Exception as e:
        logger.error(f"Error reading status: {e}")
        return jsonify({"status": "unknown"}), 500

@app.route('/api/funding_rates', methods=['GET'])
def get_funding_rates():
    """
    Calculate 2-day average funding rates from database and return top opportunities.
    """
    try:
        # Get data from last 72 hours (3 days)
        cutoff_time = datetime.utcnow() - timedelta(hours=72)
        
        # Query all records from last 72 hours for Lighter
        recent_rates = FundingRate.query.filter(
            FundingRate.exchange == 'lighter',
            FundingRate.timestamp >= cutoff_time
        ).all()
        
        if not recent_rates:
            logger.warning("No data in database for last 72 hours.")
            return jsonify({
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            })
        
        # Group by symbol and calculate average, filtering out invalid values
        symbol_rates = {}
        for record in recent_rates:
            rate = record.rate
            # Skip None or non-finite values that would produce NaN in the frontend
            if rate is None or not isinstance(rate, (int, float)) or not math.isfinite(rate):
                logger.warning(f"Skipping invalid stored rate for symbol {record.symbol}: {rate}")
                continue

            if record.symbol not in symbol_rates:
                symbol_rates[record.symbol] = []
            symbol_rates[record.symbol].append(rate)
        
        # Calculate averages
        averages = []
        for symbol, rates in symbol_rates.items():
            if not rates:
                # Skip symbols that ended up with no valid rates
                continue

            avg_rate = sum(rates) / len(rates)

            # Guard against any remaining non-finite values
            if not math.isfinite(avg_rate):
                logger.warning(f"Computed non-finite average rate for symbol {symbol}: {avg_rate}")
                continue

            # Annualized APR = Average Hourly Rate * 24 hours * 365 days
            apr = avg_rate * 24 * 365

            if not math.isfinite(apr):
                logger.warning(f"Computed non-finite APR for symbol {symbol}: {apr}")
                continue

            averages.append({
                "symbol": symbol,
                "average_3day_rate": avg_rate,
                "apr": apr
            })
        
        # Sort for top opportunities
        # Top Long: Most negative rates (shorts pay longs)
        top_long = sorted(averages, key=lambda x: x['average_3day_rate'])
        
        # Top Short: Most positive rates (longs pay shorts)
        top_short = sorted(averages, key=lambda x: x['average_3day_rate'], reverse=True)
        
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


@app.route('/api/hyperliquid/funding_rates', methods=['GET'])
def get_hyperliquid_funding_rates():
    """
    Calculate 2-day average Hyperliquid funding rates from database and return top opportunities.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=72)

        recent_rates = FundingRate.query.filter(
            FundingRate.exchange == 'hyperliquid',
            FundingRate.timestamp >= cutoff_time
        ).all()

        if not recent_rates:
            logger.warning("No Hyperliquid data in database for last 72 hours.")
            return jsonify({
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            })

        symbol_rates = {}
        for record in recent_rates:
            rate = record.rate
            if rate is None or not isinstance(rate, (int, float)) or not math.isfinite(rate):
                logger.warning(f"Skipping invalid stored Hyperliquid rate for symbol {record.symbol}: {rate}")
                continue

            if record.symbol not in symbol_rates:
                symbol_rates[record.symbol] = []
            symbol_rates[record.symbol].append(rate)

        averages = []
        for symbol, rates in symbol_rates.items():
            if not rates:
                continue

            avg_rate = sum(rates) / len(rates)

            if not math.isfinite(avg_rate):
                logger.warning(f"Computed non-finite Hyperliquid average rate for symbol {symbol}: {avg_rate}")
                continue

            apr = avg_rate * 24 * 365

            if not math.isfinite(apr):
                logger.warning(f"Computed non-finite Hyperliquid APR for symbol {symbol}: {apr}")
                continue

            averages.append({
                "symbol": symbol,
                "average_3day_rate": avg_rate,
                "apr": apr
            })

        top_long = sorted(averages, key=lambda x: x['average_3day_rate'])
        top_short = sorted(averages, key=lambda x: x['average_3day_rate'], reverse=True)

        now = datetime.utcnow()
        next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        return jsonify({
            "top_long": top_long,
            "top_short": top_short,
            "timestamp": now.isoformat() + 'Z',
            "next_funding_time": next_funding.isoformat() + 'Z'
        })
    except Exception as e:
        logger.error(f"Error calculating Hyperliquid funding rates: {e}")
        return jsonify({
            "top_long": [],
            "top_short": [],
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "next_funding_time": None
        }), 500


@app.route('/api/hyena/funding_rates', methods=['GET'])
def get_hyena_funding_rates():
    """
    Get HyENA funding rates from database (same as hyperliquid endpoint).
    This ensures fast responses and avoids rate limiting.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=72)

        recent_rates = FundingRate.query.filter(
            FundingRate.exchange == 'hyperliquid',
            FundingRate.timestamp >= cutoff_time
        ).all()

        if not recent_rates:
            logger.warning("No Hyperliquid data in database for last 72 hours.")
            return jsonify({
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            })

        symbol_rates = {}
        for record in recent_rates:
            rate = record.rate
            if rate is None or not isinstance(rate, (int, float)) or not math.isfinite(rate):
                logger.warning(f"Skipping invalid stored Hyperliquid rate for symbol {record.symbol}: {rate}")
                continue

            if record.symbol not in symbol_rates:
                symbol_rates[record.symbol] = []
            symbol_rates[record.symbol].append(rate)

        averages = []
        for symbol, rates in symbol_rates.items():
            if not rates:
                continue

            avg_rate = sum(rates) / len(rates)

            if not math.isfinite(avg_rate):
                logger.warning(f"Computed non-finite Hyperliquid average rate for symbol {symbol}: {avg_rate}")
                continue

            apr = avg_rate * 24 * 365

            if not math.isfinite(apr):
                logger.warning(f"Computed non-finite Hyperliquid APR for symbol {symbol}: {apr}")
                continue

            averages.append({
                "symbol": symbol,
                "average_3day_rate": avg_rate,
                "apr": apr
            })

        top_long = sorted(averages, key=lambda x: x['average_3day_rate'])
        top_short = sorted(averages, key=lambda x: x['average_3day_rate'], reverse=True)

        now = datetime.utcnow()
        next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        return jsonify({
            "top_long": top_long,
            "top_short": top_short,
            "timestamp": now.isoformat() + 'Z',
            "next_funding_time": next_funding.isoformat() + 'Z'
        })
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error fetching HyENA funding rates from database: {exc}")
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
            FundingRate.exchange == 'lighter',
            FundingRate.symbol == symbol,
            FundingRate.timestamp >= cutoff_time
        ).order_by(FundingRate.timestamp.asc()).all()
        
        if not history:
            logger.warning(f"No history found for symbol: {symbol}")
        
        return jsonify([item.to_dict() for item in history])
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return jsonify([]), 500


@app.route('/api/hyperliquid/funding_rates/<symbol>', methods=['GET'])
def get_hyperliquid_symbol_history(symbol):
    """
    Get historical Hyperliquid funding rates for a specific symbol.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        symbol = symbol.upper()

        history = FundingRate.query.filter(
            FundingRate.exchange == 'hyperliquid',
            FundingRate.symbol == symbol,
            FundingRate.timestamp >= cutoff_time
        ).order_by(FundingRate.timestamp.asc()).all()

        if not history:
            logger.warning(f"No Hyperliquid history found for symbol: {symbol}")

        return jsonify([item.to_dict() for item in history])
    except Exception as e:
        logger.error(f"Error fetching Hyperliquid history for {symbol}: {e}")
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
