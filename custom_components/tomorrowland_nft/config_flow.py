"""Config flow for the Tomorrowland NFT integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .api import InvalidCurrencyError, TomorrowlandNftApi, TomorrowlandNftError
from .const import (
    COLLECTIONS,
    COMMON_CURRENCIES,
    CONF_COLLECTIONS,
    CONF_CURRENCY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import TomorrowlandNftConfigEntry

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CURRENCY): SelectSelector(
            SelectSelectorConfig(
                options=[SelectOptionDict(value=c, label=c.upper()) for c in COMMON_CURRENCIES],
                custom_value=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_COLLECTIONS): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=symbol, label=name)
                    for symbol, name in COLLECTIONS.items()
                ],
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Required(CONF_SCAN_INTERVAL): NumberSelector(
            NumberSelectorConfig(
                min=MIN_SCAN_INTERVAL,
                max=MAX_SCAN_INTERVAL,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement=UnitOfTime.MINUTES,
            )
        ),
    }
)


def _defaults(hass: HomeAssistant) -> dict[str, Any]:
    return {
        CONF_CURRENCY: (hass.config.currency or "EUR").lower(),
        CONF_COLLECTIONS: list(COLLECTIONS),
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    }


async def _validate(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Normalize the input and check the currency against CoinGecko."""
    options = {
        CONF_CURRENCY: user_input[CONF_CURRENCY].strip().lower(),
        CONF_COLLECTIONS: [s for s in user_input[CONF_COLLECTIONS] if s in COLLECTIONS],
        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
    }
    if not options[CONF_COLLECTIONS]:
        return options, {CONF_COLLECTIONS: "no_collections"}

    api = TomorrowlandNftApi(async_get_clientsession(hass))
    try:
        await api.sol_price(options[CONF_CURRENCY])
    except InvalidCurrencyError:
        return options, {CONF_CURRENCY: "invalid_currency"}
    except TomorrowlandNftError:
        return options, {"base": "cannot_connect"}
    return options, {}


class TomorrowlandNftConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pick a currency, the collections to track and the poll interval."""
        errors: dict[str, str] = {}
        if user_input is not None:
            options, errors = await _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="Tomorrowland NFT", data={}, options=options)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                SCHEMA, user_input or _defaults(self.hass)
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: TomorrowlandNftConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return TomorrowlandNftOptionsFlow()


class TomorrowlandNftOptionsFlow(OptionsFlow):
    """Change currency, collections or poll interval after setup."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the same form as the initial setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            options, errors = await _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                SCHEMA, user_input or {**_defaults(self.hass), **self.config_entry.options}
            ),
            errors=errors,
        )
