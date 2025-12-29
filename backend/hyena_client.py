import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class HyenaClient:
    """
    Adapter that powers the existing "HyENA" frontend tab using Hyperliquid
    funding data via the official Hyperliquid Python SDK.

    It fetches funding history for a configured set of coins over a recent
    window (default 72 hours), computes average funding rates and APR, and
    returns "top_long" / "top_short" in the same normalized shape that the
    frontend already expects.
    """

    def __init__(self) -> None:
        network = os.getenv("HYPERLIQUID_NETWORK", "mainnet").lower()
        if network == "testnet":
            base_url = constants.TESTNET_API_URL
        else:
            base_url = constants.MAINNET_API_URL

        # We don't need websockets for this use-case.
        self.info = Info(base_url=base_url, skip_ws=True)

        # Determine which perp markets to track by loading the full perp
        # universe from Info.meta(). If this fails or returns no coins, the
        # error will propagate so it can be noticed and fixed instead of
        # silently falling back to a partial list.
        meta = self.info.meta()
        universe = meta.get("universe", []) if isinstance(meta, dict) else []
        self.coins: List[str] = [
            entry.get("name")
            for entry in universe
            if isinstance(entry, dict) and entry.get("name")
        ]
        if not self.coins:
            raise ValueError("No perp coins found in Hyperliquid meta() response")
        logger.info("Tracking all %d Hyperliquid markets", len(self.coins))

        # Rate limiting: track last request time to avoid 429s
        self._last_request_time = 0.0
        self._min_request_interval = float(os.getenv("HYPERLIQUID_MIN_REQUEST_INTERVAL", "1.0"))  # seconds between requests

        # Window (in hours) over which to average funding.
        self.lookback_hours = int(os.getenv("HYPERLIQUID_FUNDING_LOOKBACK_HOURS", "72"))

    def _fetch_coin_funding_history(self, coin: str, start_ms: int, end_ms: int) -> List[Dict[str, Any]]:
        """Fetch raw funding history for a single coin using the SDK.

        The Info class exposes a fundingHistory helper that posts
        {"type": "fundingHistory", ...} under the hood and returns a list of
        records with: coin, fundingRate, premium, time.
        """
        try:
            # Rate limiting: ensure minimum interval between requests
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                sleep_time = self._min_request_interval - time_since_last
                logger.debug("Rate limiting: sleeping %.2f seconds before fetching %s", sleep_time, coin)
                time.sleep(sleep_time)
            
            # Update last request time before making the API call
            self._last_request_time = time.time()
            
            # The SDK method is named funding_history(name, startTime, endTime).
            # We rely on the Info.name_to_coin mapping to resolve the name.
            return self.info.funding_history(coin, start_ms, end_ms)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching funding history for %s: %s", coin, exc)
            return []

    def _average_funding_rate(self, records: List[Dict[str, Any]]) -> float | None:
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

    def fetch_funding_rates(self) -> Dict[str, Any]:
        """Fetch current Hyperliquid funding data and normalize to frontend shape."""
        try:
            now = datetime.utcnow()
            end_ms = int(now.timestamp() * 1000)
            start_ms = int((now - timedelta(hours=self.lookback_hours)).timestamp() * 1000)

            processed: List[Dict[str, Any]] = []
            
            # For quick response, process only first 50 markets
            # This ensures the API returns quickly while still providing useful data
            quick_fetch_coins = self.coins[:50]
            logger.info("Quick fetching funding rates for first %d markets", len(quick_fetch_coins))
            
            for coin in quick_fetch_coins:
                history = self._fetch_coin_funding_history(coin, start_ms, end_ms)
                avg_rate = self._average_funding_rate(history)
                if avg_rate is None:
                    logger.debug("No valid funding data for coin %s", coin)
                    continue

                apr = avg_rate * 24 * 365
                processed.append(
                    {
                        "symbol": coin,
                        "average_3day_rate": avg_rate,
                        "apr": apr,
                    }
                )

            if not processed:
                logger.warning("Hyperliquid SDK returned no usable funding data.")
                return {
                    "top_long": [],
                    "top_short": [],
                    "timestamp": now.isoformat() + "Z",
                    "next_funding_time": None,
                }

            top_long = sorted(processed, key=lambda x: x["average_3day_rate"])
            top_short = sorted(processed, key=lambda x: x["average_3day_rate"], reverse=True)
            
            # Assume hourly funding: next funding is the start of the next hour
            next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            
            return {
                "top_long": top_long,
                "top_short": top_short,
                "timestamp": now.isoformat() + "Z",
                "next_funding_time": next_funding.isoformat() + "Z",
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching Hyperliquid funding rates: %s", exc)
            return {
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "next_funding_time": None,
            }
    
    def fetch_all_funding_rates(self) -> Dict[str, Any]:
        """Fetch ALL Hyperliquid funding data (slower, for background jobs)."""
        try:
            now = datetime.utcnow()
            end_ms = int(now.timestamp() * 1000)
            start_ms = int((now - timedelta(hours=self.lookback_hours)).timestamp() * 1000)

            processed: List[Dict[str, Any]] = []
            logger.info("Fetching ALL funding rates for %d markets (this will take ~%d seconds)", 
                       len(self.coins), len(self.coins))
            
            for coin in self.coins:
                history = self._fetch_coin_funding_history(coin, start_ms, end_ms)
                avg_rate = self._average_funding_rate(history)
                if avg_rate is None:
                    logger.debug("No valid funding data for coin %s", coin)
                    continue

                apr = avg_rate * 24 * 365
                processed.append(
                    {
                        "symbol": coin,
                        "average_3day_rate": avg_rate,
                        "apr": apr,
                    }
                )

            if not processed:
                logger.warning("Hyperliquid SDK returned no usable funding data.")
                return {
                    "top_long": [],
                    "top_short": [],
                    "timestamp": now.isoformat() + "Z",
                    "next_funding_time": None,
                }

            top_long = sorted(processed, key=lambda x: x["average_3day_rate"])
            top_short = sorted(processed, key=lambda x: x["average_3day_rate"], reverse=True)
            
            # Assume hourly funding: next funding is the start of the next hour
            next_funding = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            
            return {
                "top_long": top_long,
                "top_short": top_short,
                "timestamp": now.isoformat() + "Z",
                "next_funding_time": next_funding.isoformat() + "Z",
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching ALL Hyperliquid funding rates: %s", exc)
            return {
                "top_long": [],
                "top_short": [],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "next_funding_time": None,
            }
