import logging
import os
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

        # Basic default universe. You can override this with HYPERLIQUID_COINS
        # (comma-separated list) in the environment if you want a custom list.
        coins_env = os.getenv("HYPERLIQUID_COINS")
        if coins_env:
            self.coins: List[str] = [c.strip() for c in coins_env.split(",") if c.strip()]
        else:
            # These names must match Hyperliquid's naming (e.g. "ETH", "BTC")
            self.coins = [
                "BTC",
                "ETH",
                "SOL",
                "OP",
                "ARB",
                "LINK",
                "DOGE",
                "BNB",
            ]

        # Window (in hours) over which to average funding.
        self.lookback_hours = int(os.getenv("HYPERLIQUID_FUNDING_LOOKBACK_HOURS", "72"))

    def _fetch_coin_funding_history(self, coin: str, start_ms: int, end_ms: int) -> List[Dict[str, Any]]:
        """Fetch raw funding history for a single coin using the SDK.

        The Info class exposes a fundingHistory helper that posts
        {"type": "fundingHistory", ...} under the hood and returns a list of
        records with: coin, fundingRate, premium, time.
        """
        try:
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

            top_long = sorted(processed, key=lambda x: x["average_3day_rate"])[:10]
            top_short = sorted(processed, key=lambda x: x["average_3day_rate"], reverse=True)[:10]

            next_funding = (now.replace(minute=0, second=0, microsecond=0))

            return {
                "top_long": top_long,
                "top_short": top_short,
                "timestamp": now.isoformat() + "Z",
                "next_funding_time": next_funding.isoformat() + "Z",
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to fetch Hyperliquid funding rates: %s", exc)
            now = datetime.utcnow()
            return {
                "top_long": [],
                "top_short": [],
                "timestamp": now.isoformat() + "Z",
                "next_funding_time": None,
            }
