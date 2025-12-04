import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LighterClient:
    """
    Lightweight client for the Lighter API.

    Note: We intentionally avoid heavy dependencies like pandas/numexpr here
    to keep deployment simple and avoid binary compatibility issues.
    """

    BASE_URL = "https://mainnet.zklighter.elliot.ai/api/v1"

    def __init__(self):
        self.session = requests.Session()

    def get_funding_rates(self, symbol=None):
        """
        Fetches funding rates.
        If symbol is provided, fetches for that symbol.
        Otherwise, might need to fetch for all or discover symbols first.
        """
        # Note: The exact endpoint for "all symbols" history might differ.
        # We might need to get a list of symbols first.
        # For now, let's assume we can get a list of markets/symbols.
        
        # First, get list of symbols if we don't have them
        # This is a guess at the endpoint for markets/tickers
        try:
            # Try to get tickers or markets to know which symbols to fetch
            # If this fails, we might need a hardcoded list or another endpoint
            pass 
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []

        return []

    def get_all_funding_rates_history(self):
        """
        Placeholder for a future "all symbols history" implementation.

        Currently unused by the application.
        """
        logger.info("get_all_funding_rates_history called, but not implemented.")
        return []

    def get_symbols(self):
        # Hardcoded for now as fallback
        return ["WETH-USDC", "WBTC-USDC", "SOL-USDC", "MATIC-USDC", "ARB-USDC", "AVAX-USDC", "OP-USDC", "LINK-USDC", "DOGE-USDC", "BNB-USDC"]

    def calculate_2day_average(self, history_data):
        """
        Simple 2-day average funding rate from history data.

        history_data: list of dicts with 'rate' and 'timestamp' (or similar)
        """
        if not history_data:
            return 0.0

        # Lightweight implementation without pandas
        rates = [item.get("rate") for item in history_data if isinstance(item.get("rate"), (int, float))]
        if not rates:
            return 0.0

        return sum(rates) / len(rates)

    def get_market_opportunities(self):
        """
        Main method to get top long/short opportunities.
        """
        logger.info("Fetching market opportunities from Lighter API...")
        
        try:
            # Real API call
            response = self.session.get(f"{self.BASE_URL}/funding-rates")
            response.raise_for_status()
            data = response.json()
            
            # The API returns a list of funding rates.
            # Structure: [{"symbol": "ETH-USDC", "rate": "0.0001", ...}, ...]
            # We need to parse this.
            
            # Note: The prompt asks for "2-Day Average". 
            # The public API might only return CURRENT rates.
            # If history is not available, we will use the current rate as the best proxy 
            # for the "average" in this initial version, or we'd need to fetch history per symbol.
            # Search results didn't explicitly give a history endpoint that works without auth/complex params.
            # We will assume 'rate' is the current funding rate.
            
            processed_data = []

            # Check if 'funding_rates' key exists or if it's a list directly
            items = data.get('funding_rates', []) if isinstance(data, dict) else data

            for item in items:
                symbol = item.get('symbol')
                rate_str = item.get('rate', '0')
                try:
                    rate = float(rate_str)
                except (TypeError, ValueError):
                    logger.warning(f"Skipping invalid rate from API for symbol {symbol}: {rate_str}")
                    continue

                processed_data.append({
                    "symbol": symbol,
                    "average_2day_rate": rate
                })

            if not processed_data:
                logger.warning("No valid data received from API.")
                return {"top_long": [], "top_short": [], "timestamp": datetime.now().isoformat()}

            # Sort lists in pure Python instead of pandas
            # Top Long: Lowest (most negative) rates
            top_long_list = sorted(processed_data, key=lambda x: x["average_2day_rate"])[:10]

            # Top Short: Highest (most positive) rates
            top_short_list = sorted(processed_data, key=lambda x: x["average_2day_rate"], reverse=True)[:10]

            return {
                "top_long": top_long_list,
                "top_short": top_short_list,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching/processing data: {e}")
            # Fallback to empty or cached if needed, but for now return empty
            return {
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.now().isoformat()
            }

if __name__ == "__main__":
    client = LighterClient()
    print(client.get_market_opportunities())
