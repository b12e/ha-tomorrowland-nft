"""Clients for Magic Eden (floor prices) and CoinGecko (SOL exchange rate)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any

import aiohttp

from .const import COINGECKO_URL, LAMPORTS_PER_SOL, MAGIC_EDEN_URL

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "HomeAssistant-TomorrowlandNFT/0.1 (+https://github.com/b12e/ha-tomorrowland-nft)",
}

# Magic Eden allows 2 requests per second on the public API. Leave headroom so
# a burst of collection lookups never trips the limit.
MAGIC_EDEN_MIN_INTERVAL = 0.6


class TomorrowlandNftError(Exception):
    """Base error for API failures."""


class RateLimitedError(TomorrowlandNftError):
    """The upstream API returned HTTP 429."""

    def __init__(self, service: str, retry_after: int | None) -> None:
        """Store the service name and the server's Retry-After hint."""
        super().__init__(f"{service} rate limit hit (retry after {retry_after}s)")
        self.service = service
        self.retry_after = retry_after


class InvalidCurrencyError(TomorrowlandNftError):
    """CoinGecko does not know the requested currency."""


@dataclass(frozen=True, slots=True)
class CollectionStats:
    """Market stats for one collection, with prices in SOL."""

    floor_price: float | None
    listed_count: int | None
    avg_price_24h: float | None
    volume_7d: float | None


def _lamports_to_sol(value: Any) -> float | None:
    if value is None:
        return None
    return float(value) / LAMPORTS_PER_SOL


class TomorrowlandNftApi:
    """Fetches collection stats and the SOL price."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize with a shared aiohttp session."""
        self._session = session
        self._magic_eden_lock = asyncio.Lock()
        self._magic_eden_last = 0.0

    async def _get(self, service: str, url: str, params: dict[str, str] | None = None) -> Any:
        try:
            async with self._session.get(
                url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status == 429:
                    retry_after = resp.headers.get("Retry-After")
                    raise RateLimitedError(
                        service, int(retry_after) if retry_after and retry_after.isdigit() else None
                    )
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise TomorrowlandNftError(f"{service} request failed: {err}") from err

    async def collection_stats(self, symbol: str) -> CollectionStats:
        """Return floor price and volume stats for a Magic Eden collection."""
        async with self._magic_eden_lock:
            wait = self._magic_eden_last + MAGIC_EDEN_MIN_INTERVAL - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                data = await self._get("Magic Eden", f"{MAGIC_EDEN_URL}/collections/{symbol}/stats")
            finally:
                self._magic_eden_last = time.monotonic()

        if not isinstance(data, dict):
            raise TomorrowlandNftError(f"Unexpected Magic Eden response for {symbol}")
        return CollectionStats(
            floor_price=_lamports_to_sol(data.get("floorPrice")),
            listed_count=data.get("listedCount"),
            avg_price_24h=_lamports_to_sol(data.get("avgPrice24hr")),
            volume_7d=_lamports_to_sol(data.get("volume7d")),
        )

    async def sol_price(self, currency: str) -> float:
        """Return the price of 1 SOL in the given currency (CoinGecko vs_currency)."""
        data = await self._get(
            "CoinGecko",
            f"{COINGECKO_URL}/simple/price",
            {"ids": "solana", "vs_currencies": currency},
        )
        try:
            return float(data["solana"][currency])
        except (KeyError, TypeError, ValueError) as err:
            raise InvalidCurrencyError(f"CoinGecko has no SOL price in {currency!r}") from err
