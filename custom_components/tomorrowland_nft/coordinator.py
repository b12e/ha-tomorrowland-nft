"""Data update coordinator for the Tomorrowland NFT integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CollectionStats, TomorrowlandNftApi, TomorrowlandNftError
from .const import (
    COLLECTIONS,
    CONF_COLLECTIONS,
    CONF_CURRENCY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)

type TomorrowlandNftConfigEntry = ConfigEntry[TomorrowlandNftCoordinator]


@dataclass(frozen=True, slots=True)
class TomorrowlandNftData:
    """One poll's worth of data."""

    sol_price: float
    collections: dict[str, CollectionStats]


class TomorrowlandNftCoordinator(DataUpdateCoordinator[TomorrowlandNftData]):
    """Polls floor prices for the selected collections and the SOL rate."""

    config_entry: TomorrowlandNftConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TomorrowlandNftConfigEntry,
        api: TomorrowlandNftApi,
    ) -> None:
        """Initialize from the config entry options."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.api = api
        self.currency: str = entry.options[CONF_CURRENCY]
        self.symbols: list[str] = [
            symbol
            for symbol in entry.options.get(CONF_COLLECTIONS, list(COLLECTIONS))
            if symbol in COLLECTIONS
        ]

    async def _async_update_data(self) -> TomorrowlandNftData:
        try:
            sol_price = await self.api.sol_price(self.currency)
            collections = {
                symbol: await self.api.collection_stats(symbol) for symbol in self.symbols
            }
        except TomorrowlandNftError as err:
            raise UpdateFailed(str(err)) from err
        return TomorrowlandNftData(sol_price=sol_price, collections=collections)
