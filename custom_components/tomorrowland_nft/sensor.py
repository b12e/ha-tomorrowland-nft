"""Floor price sensors for the Tomorrowland NFT collections."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CollectionStats
from .const import COLLECTIONS, DOMAIN, MAGIC_EDEN_MARKETPLACE_URL
from .coordinator import (
    TomorrowlandNftConfigEntry,
    TomorrowlandNftCoordinator,
    TomorrowlandNftData,
)

PARALLEL_UPDATES = 0

SOL = "SOL"


@dataclass(frozen=True, kw_only=True)
class FloorPriceDescription(SensorEntityDescription):
    """Describes a floor price sensor."""

    in_currency: bool
    value_fn: Callable[[CollectionStats, TomorrowlandNftData], float | None]
    attrs_fn: Callable[[CollectionStats, TomorrowlandNftData], dict[str, Any]]


def _in_currency(price: float | None, data: TomorrowlandNftData) -> float | None:
    return None if price is None else price * data.sol_price


SENSORS: tuple[FloorPriceDescription, ...] = (
    FloorPriceDescription(
        key="floor_price_sol",
        translation_key="floor_price_sol",
        native_unit_of_measurement=SOL,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        in_currency=False,
        value_fn=lambda stats, _: stats.floor_price,
        attrs_fn=lambda stats, _: {
            "listed_count": stats.listed_count,
            "avg_price_24h": stats.avg_price_24h,
            "volume_7d": stats.volume_7d,
        },
    ),
    FloorPriceDescription(
        key="floor_price_currency",
        translation_key="floor_price_currency",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        in_currency=True,
        value_fn=lambda stats, data: _in_currency(stats.floor_price, data),
        attrs_fn=lambda stats, data: {
            "sol_price": data.sol_price,
            "avg_price_24h": _in_currency(stats.avg_price_24h, data),
            "volume_7d": _in_currency(stats.volume_7d, data),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TomorrowlandNftConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create a SOL and a currency floor price sensor per collection."""
    coordinator = entry.runtime_data
    async_add_entities(
        FloorPriceSensor(coordinator, symbol, description)
        for symbol in coordinator.symbols
        for description in SENSORS
    )


class FloorPriceSensor(CoordinatorEntity[TomorrowlandNftCoordinator], SensorEntity):
    """Floor price of one collection, in SOL or in the configured currency."""

    _attr_has_entity_name = True
    entity_description: FloorPriceDescription

    def __init__(
        self,
        coordinator: TomorrowlandNftCoordinator,
        symbol: str,
        description: FloorPriceDescription,
    ) -> None:
        """Initialize the sensor for one collection."""
        super().__init__(coordinator)
        self.entity_description = description
        self._symbol = symbol
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{symbol}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, symbol)},
            name=COLLECTIONS[symbol],
            manufacturer="Tomorrowland",
            model="Solana NFT collection",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=f"{MAGIC_EDEN_MARKETPLACE_URL}/{symbol}",
        )
        if description.in_currency:
            currency = coordinator.currency.upper()
            self._attr_native_unit_of_measurement = currency
            self._attr_translation_placeholders = {"currency": currency}

    @property
    def _stats(self) -> CollectionStats | None:
        return self.coordinator.data.collections.get(self._symbol)

    @property
    def available(self) -> bool:
        """Unavailable when the last poll failed or skipped this collection."""
        return super().available and self._stats is not None

    @property
    def native_value(self) -> float | None:
        """Return the floor price, or None when nothing is listed."""
        stats = self._stats
        return (
            None
            if stats is None
            else self.entity_description.value_fn(stats, self.coordinator.data)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return listing and volume stats alongside the floor price."""
        stats = self._stats
        return (
            None
            if stats is None
            else self.entity_description.attrs_fn(stats, self.coordinator.data)
        )
