"""Fixtures for the Tomorrowland NFT tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.tomorrowland_nft.const import COINGECKO_URL, MAGIC_EDEN_URL

STATS = {
    "tomorrowland_winter": {
        "floorPrice": 47_399_000_000,
        "listedCount": 28,
        "avgPrice24hr": 46_991_000_000,
        "volume7d": 611_563_800_000,
    },
    "the_reflection_of_love": {
        "floorPrice": 15_680_800_000,
        "listedCount": 39,
        "avgPrice24hr": 15_349_300_000,
        "volume7d": 262_494_090_000,
    },
    "tomorrowland_love_unity": {"listedCount": 0},
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    return


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    """Skip the Magic Eden spacing so tests run instantly."""
    monkeypatch.setattr("custom_components.tomorrowland_nft.api.MAGIC_EDEN_MIN_INTERVAL", 0)


@pytest.fixture
def mock_apis(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock CoinGecko (EUR only) and Magic Eden stats."""
    aioclient_mock.get(
        f"{COINGECKO_URL}/simple/price",
        params={"ids": "solana", "vs_currencies": "eur"},
        json={"solana": {"eur": 100.0}},
    )
    aioclient_mock.get(
        f"{COINGECKO_URL}/simple/price",
        params={"ids": "solana", "vs_currencies": "xyz"},
        json={},
    )
    for symbol, body in STATS.items():
        aioclient_mock.get(
            f"{MAGIC_EDEN_URL}/collections/{symbol}/stats", json={"symbol": symbol, **body}
        )
    return aioclient_mock
