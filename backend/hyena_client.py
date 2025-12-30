"""
HyenaClient - Fetches funding rates from HyENA's USDe-margined perpetual DEX.

HyENA is built on Hyperliquid's HIP-3 (Builder-Deployed Perpetuals) framework.
It uses USDe (Ethena's stablecoin) as collateral instead of USDC.

API Details:
- Dex name: "hyna"
- Coins are prefixed: "hyna:BTC", "hyna:ETH", etc.
- Uses the same Hyperliquid API endpoints with "dex" parameter
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Hyperliquid API base URL
HYPERLIQUID_API_URL = "https://api.hyperliquid.xyz/info"

# HyENA's dex identifier on Hyperliquid
HYENA_DEX_NAME = "hyna"


class HyenaClient:
    """
    Client for fetching funding rates from HyENA's USDe-margined perpetual DEX.
    
    HyENA leverages Hyperliquid's HIP-3 framework, allowing us to query
    funding data via the standard Hyperliquid API with the "dex" parameter.
    """

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = float(
            os.getenv("HYENA_MIN_REQUEST_INTERVAL", "0.5")
        )
        
        # Window (in hours) over which to average funding
        self.lookback_hours = int(os.getenv("HYENA_FUNDING_LOOKBACK_HOURS", "72"))
        
        # Fetch available coins on initialization
        self.coins: List[str] = []
        self._load_coins()

    def _rate_limit(self) -> None:
        """Ensure minimum interval between API requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug("Rate limiting: sleeping %.2f seconds", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _post(self, payload: Dict[str, Any]) -> Any:
        """Make a POST request to the Hyperliquid API with rate limiting."""
        self._rate_limit()
        try:
            response = self.session.post(HYPERLIQUID_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error("API request failed: %s", exc)
            raise

    def _load_coins(self) -> None:
        """Load available coins from HyENA's perp dex universe."""
        try:
            # Fetch HyENA-specific metadata
            meta = self._post({"type": "meta", "dex": HYENA_DEX_NAME})
            universe = meta.get("universe", []) if isinstance(meta, dict) else []
            
            # Extract coin names, filtering out delisted coins
            self.coins = [
                entry.get("name")
                for entry in universe
                if isinstance(entry, dict) 
                and entry.get("name")
                and not entry.get("isDelisted", False)
            ]
            
            if not self.coins:
                logger.warning("No active coins found in HyENA dex")
            else:
                logger.info(
                    "Loaded %d active HyENA coins: %s", 
                    len(self.coins), 
                    ", ".join(self.coins)
                )
        except Exception as exc:
            logger.error("Failed to load HyENA coins: %s", exc)
            # Fallback to known coins if API fails
            self.coins = ["hyna:BTC", "hyna:ETH", "hyna:SOL", "hyna:HYPE"]
            logger.info("Using fallback coin list: %s", self.coins)

    def _fetch_coin_funding_history(
        self, coin: str, start_ms: int, end_ms: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch funding history for a single HyENA coin."""
        try:
            payload: Dict[str, Any] = {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": start_ms,
            }
            if end_ms is not None:
                payload["endTime"] = end_ms
            
            result = self._post(payload)
            return result if isinstance(result, list) else []
        except Exception as exc:
            logger.error("Error fetching funding history for %s: %s", coin, exc)
            return []

    def _average_funding_rate(self, records: List[Dict[str, Any]]) -> Optional[float]:
        """Compute the simple average fundingRate from a list of records."""
        if not records:
            return None

        rates: List[float] = []
        for item in records:
            raw_rate = item.get("fundingRate")
            try:
                rate = float(raw_rate)
            except (TypeError, ValueError):
                continue
            rates.append(rate)

        if not rates:
            return None

        return sum(rates) / len(rates)

    def _format_symbol(self, coin: str) -> str:
        """
        Format HyENA coin name for display.
        
        Converts "hyna:BTC" to "BTC" for cleaner frontend display.
        """
        if coin.startswith("hyna:"):
            return coin[5:]  # Remove "hyna:" prefix
        return coin

    def fetch_funding_rates(self) -> Dict[str, Any]:
        """
        Fetch current HyENA funding data and normalize to frontend shape.
        
        This is the quick version that fetches all available coins
        (HyENA typically has fewer coins than mainnet Hyperliquid).
        """
        try:
            now = datetime.utcnow()
            end_ms = int(now.timestamp() * 1000)
            start_ms = int((now - timedelta(hours=self.lookback_hours)).timestamp() * 1000)

            processed: List[Dict[str, Any]] = []
            logger.info("Fetching HyENA funding rates for %d coins", len(self.coins))

            for coin in self.coins:
                history = self._fetch_coin_funding_history(coin, start_ms, end_ms)
                avg_rate = self._average_funding_rate(history)
                
                if avg_rate is None:
                    logger.debug("No valid funding data for coin %s", coin)
                    continue

                apr = avg_rate * 24 * 365
                processed.append({
                    "symbol": self._format_symbol(coin),
                    "average_3day_rate": avg_rate,
                    "apr": apr,
                })

            if not processed:
                logger.warning("HyENA returned no usable funding data.")
                return {
                    "top_long": [],
                    "top_short": [],
                    "timestamp": now.isoformat() + "Z",
                    "next_funding_time": None,
                }

            # Sort for opportunities
            top_long = sorted(processed, key=lambda x: x["average_3day_rate"])
            top_short = sorted(processed, key=lambda x: x["average_3day_rate"], reverse=True)

            # Next funding is the start of the next hour (hourly funding)
            next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

            return {
                "top_long": top_long,
                "top_short": top_short,
                "timestamp": now.isoformat() + "Z",
                "next_funding_time": next_funding.isoformat() + "Z",
            }
        except Exception as exc:
            logger.error("Error fetching HyENA funding rates: %s", exc)
            return {
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "next_funding_time": None,
            }

    def fetch_all_funding_rates(self) -> Dict[str, Any]:
        """
        Fetch ALL HyENA funding data.
        
        For HyENA, this is the same as fetch_funding_rates() since the coin
        count is small. Kept for API compatibility with the background job.
        """
        return self.fetch_funding_rates()
