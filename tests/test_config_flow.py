"""Config and options flow tests."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.tomorrowland_nft.const import (
    COLLECTIONS,
    CONF_COLLECTIONS,
    CONF_CURRENCY,
    DOMAIN,
)


async def test_user_flow(hass: HomeAssistant, mock_apis) -> None:
    """A valid currency creates the entry with normalized options."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CURRENCY: " EUR ", CONF_COLLECTIONS: list(COLLECTIONS), CONF_SCAN_INTERVAL: 5.0},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {
        CONF_CURRENCY: "eur",
        CONF_COLLECTIONS: list(COLLECTIONS),
        CONF_SCAN_INTERVAL: 5,
    }


async def test_invalid_currency(hass: HomeAssistant, mock_apis) -> None:
    """A currency CoinGecko does not price SOL in is rejected."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CURRENCY: "xyz", CONF_COLLECTIONS: list(COLLECTIONS), CONF_SCAN_INTERVAL: 5},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_CURRENCY: "invalid_currency"}


async def test_no_collections(hass: HomeAssistant, mock_apis) -> None:
    """At least one collection is required."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CURRENCY: "eur", CONF_COLLECTIONS: [], CONF_SCAN_INTERVAL: 5},
    )
    assert result["errors"] == {CONF_COLLECTIONS: "no_collections"}
