# Tomorrowland NFT for Home Assistant

<img src="custom_components/tomorrowland_nft/brand/icon@2x.png" width="96" align="right" alt="">

A HACS integration that tracks the floor price of the Tomorrowland Solana NFT
collections (the pieces of the Medallion of Memoria) on Magic Eden, in SOL and in a
currency of your choice.

| Collection | Magic Eden symbol |
| --- | --- |
| A Letter from the Universe (Winter) | [`tomorrowland_winter`](https://magiceden.io/marketplace/tomorrowland_winter) |
| The Reflection of Love | [`the_reflection_of_love`](https://magiceden.io/marketplace/the_reflection_of_love) |
| The Symbol of Love and Unity | [`tomorrowland_love_unity`](https://magiceden.io/marketplace/tomorrowland_love_unity) |

## Entities

Each collection is a service device with two sensors:

| Entity | Example | Attributes |
| --- | --- | --- |
| `sensor.<collection>_floor_price_sol` | `47.399 SOL` | `listed_count`, `avg_price_24h`, `volume_7d` (SOL) |
| `sensor.<collection>_floor_price_<currency>` | `4638.94 EUR` | `sol_price`, `avg_price_24h`, `volume_7d` (currency) |

A separate **Solana** device holds the exchange rate itself:

| Entity | Example |
| --- | --- |
| `sensor.solana_price_<currency>` | `97.87 EUR` |

All sensors use `state_class: measurement`, so they get long-term statistics.
A collection with nothing listed reports `unknown` rather than `0`.

## Installation

1. In HACS, open the menu, choose **Custom repositories** and add
   `https://github.com/b12e/ha-tomorrowland-nft` as an **Integration**.
2. Install **Tomorrowland NFT** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Tomorrowland NFT**.

## Configuration

| Option | Default | Notes |
| --- | --- | --- |
| Currency | Your Home Assistant currency | Any [CoinGecko vs_currency](https://api.coingecko.com/api/v3/simple/supported_vs_currencies) (`eur`, `usd`, `btc`, ...). Checked against CoinGecko when you save. |
| Collections | All three | Only selected collections get sensors. |
| Update interval | 5 minutes | 1 to 60 minutes. |

All options can be changed later from the integration's **Configure** button.

## Data sources and rate limits

- **Floor prices:** Magic Eden public API, `GET /v2/collections/{symbol}/stats`
  (prices in lamports, converted to SOL). The free tier allows 120 requests per
  minute (2 per second). The integration spaces its requests at least 0.6 s apart and
  makes one request per collection per poll, so the default settings use 0.6 requests
  per minute.
- **SOL exchange rate:** CoinGecko `GET /api/v3/simple/price`, one request per poll.

If either API fails or rate-limits a poll, the sensors become unavailable until the
next successful poll.

## Brand images

The icon ships in `custom_components/tomorrowland_nft/brand/`, which Home Assistant
2026.3 and newer picks up automatically. Older versions, and the HACS store listing,
show a placeholder icon instead.

## Development

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```

## Disclaimer

This is an unofficial community project. It is not affiliated with or endorsed by
Tomorrowland or Magic Eden. Tomorrowland and its logo are trademarks of their owner.
Floor prices are informational, not financial advice.
