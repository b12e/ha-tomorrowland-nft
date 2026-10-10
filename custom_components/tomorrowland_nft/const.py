"""Constants for the Tomorrowland NFT integration."""

from __future__ import annotations

import logging
from typing import Final

LOGGER = logging.getLogger(__package__)

DOMAIN: Final = "tomorrowland_nft"

CONF_COLLECTIONS: Final = "collections"
CONF_CURRENCY: Final = "currency"

# Minutes between polls. Each poll costs one Magic Eden request per collection
# plus one CoinGecko request, far below Magic Eden's 120 QPM public limit.
DEFAULT_SCAN_INTERVAL: Final = 5
MIN_SCAN_INTERVAL: Final = 1
MAX_SCAN_INTERVAL: Final = 60

# Magic Eden collection symbol -> display name.
COLLECTIONS: Final[dict[str, str]] = {
    "tomorrowland_winter": "A Letter from the Universe",
    "the_reflection_of_love": "The Reflection of Love",
    "tomorrowland_love_unity": "The Symbol of Love and Unity",
}

# Offered in the currency dropdown; any CoinGecko vs_currency can be typed in.
COMMON_CURRENCIES: Final = ["eur", "usd", "gbp", "chf", "brl", "aud", "cad", "jpy"]

LAMPORTS_PER_SOL: Final = 1_000_000_000

MAGIC_EDEN_URL: Final = "https://api-mainnet.magiceden.dev/v2"
MAGIC_EDEN_MARKETPLACE_URL: Final = "https://magiceden.io/marketplace"
COINGECKO_URL: Final = "https://api.coingecko.com/api/v3"
COINGECKO_SOLANA_URL: Final = "https://www.coingecko.com/en/coins/solana"
