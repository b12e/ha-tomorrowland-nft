"""Sensor tests."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_SCAN_INTERVAL, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tomorrowland_nft.const import (
    COINGECKO_URL,
    COLLECTIONS,
    CONF_COLLECTIONS,
    CONF_CURRENCY,
    DOMAIN,
    MAGIC_EDEN_URL,
)

OPTIONS = {CONF_CURRENCY: "eur", CONF_COLLECTIONS: list(COLLECTIONS), CONF_SCAN_INTERVAL: 5}


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=OPTIONS)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_floor_prices(hass: HomeAssistant, mock_apis) -> None:
    """SOL and EUR floor prices are exposed per collection."""
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    sol = hass.states.get("sensor.a_letter_from_the_universe_floor_price_sol")
    assert float(sol.state) == 47.399
    assert sol.attributes["unit_of_measurement"] == "SOL"
    assert sol.attributes["listed_count"] == 28
    assert sol.attributes["avg_price_24h"] == 46.991

    eur = hass.states.get("sensor.a_letter_from_the_universe_floor_price_eur")
    assert float(eur.state) == 4739.9
    assert eur.attributes["unit_of_measurement"] == "EUR"
    assert eur.attributes["sol_price"] == 100.0
    assert eur.attributes["friendly_name"] == "A Letter from the Universe Floor price EUR"

    assert float(hass.states.get("sensor.the_reflection_of_love_floor_price_eur").state) == 1568.08


async def test_no_listings_is_unknown(hass: HomeAssistant, mock_apis) -> None:
    """A collection with nothing listed reports unknown rather than 0."""
    await _setup(hass)
    assert (
        hass.states.get("sensor.the_symbol_of_love_and_unity_floor_price_sol").state
        == STATE_UNKNOWN
    )
    assert (
        hass.states.get("sensor.the_symbol_of_love_and_unity_floor_price_eur").state
        == STATE_UNKNOWN
    )


async def test_rate_limited_retries_setup(hass: HomeAssistant, aioclient_mock) -> None:
    """A Magic Eden 429 makes setup retry instead of failing hard."""
    aioclient_mock.get(f"{COINGECKO_URL}/simple/price", json={"solana": {"eur": 100.0}})
    aioclient_mock.get(
        f"{MAGIC_EDEN_URL}/collections/tomorrowland_winter/stats",
        status=429,
        headers={"Retry-After": "60"},
        text="You have exceeded the requests in 1 min limit!",
    )
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
