# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on the **Binance Futures USDT-M Testnet**.

---

## Features

| Feature | Details |
|---|---|
| Order types | MARKET, LIMIT, STOP\_MARKET (bonus) |
| Sides | BUY / SELL |
| CLI | `argparse`-powered with descriptive help text |
| Logging | Rotating file log (DEBUG) + coloured console (INFO) |
| Validation | Comprehensive input checks before any API call |
| Error handling | BinanceAPIError, network errors, validation errors |
| Structure | Strict separation: `client` → `orders` → `cli` |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (HMAC-SHA256 signing)
│   ├── orders.py          # Order placement logic (dispatcher + per-type functions)
│   ├── validators.py      # Input validation (raises ValueError on bad input)
│   └── logging_config.py  # Rotating file + console handlers
├── cli.py                 # CLI entry point (argparse sub-commands)
├── logs/
│   └── trading_bot.log    # Auto-created on first run
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / unzip the project

```bash
cd trading_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Register on Binance Futures Testnet

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in / register (separate from your main Binance account)
3. Navigate to **API Management** → generate a new API key pair
4. Copy the **API Key** and **Secret Key**

### 5. Set environment variables

```bash
# Linux / macOS
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_secret_here"

# Windows (PowerShell)
$env:BINANCE_TESTNET_API_KEY="your_api_key_here"
$env:BINANCE_TESTNET_API_SECRET="your_secret_here"
```

> The bot reads credentials **only** from environment variables — they are never hard-coded or stored on disk.

---

## How to Run

### Check connectivity

```bash
python cli.py ping
```

```
✔ Connected to Binance Futures Testnet
  Server time: 1746691921423 ms
```

### View account balances

```bash
python cli.py account
```

### Place a MARKET order

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

**Output:**
```
────────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
────────────────────────────────────────────────────────────
  ORDER RESPONSE DETAILS
────────────────────────────────────────────────────────────
  orderId      : 4729301823
  clientOrderId: web_xKd8Aj2m1pQn
  status       : FILLED
  executedQty  : 0.001
  avgPrice     : 96432.10
  ...
────────────────────────────────────────────────────────────
✔ Order placed successfully!
```

### Place a LIMIT order

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 98000
```

### Place a STOP_MARKET order (bonus)

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side SELL \
  --type STOP_MARKET \
  --quantity 0.001 \
  --stop-price 90000
```

### Increase log verbosity (console)

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Logging

Logs are written to `logs/trading_bot.log` automatically.

- **File handler**: captures `DEBUG` and above — full request params, raw response bodies, error tracebacks
- **Console handler**: captures `INFO` and above by default (override with `--log-level`)
- Log files rotate at **5 MB**, keeping 3 backups

Example log lines:
```
2025-05-08 10:13:15 | INFO     | trading_bot.orders | Placing MARKET order | symbol=BTCUSDT side=BUY qty=0.001
2025-05-08 10:13:16 | DEBUG    | trading_bot.client | REQUEST  method=POST url=.../fapi/v1/order params={...}
2025-05-08 10:13:16 | DEBUG    | trading_bot.client | RESPONSE status=200 body={...}
2025-05-08 10:13:16 | INFO     | trading_bot.orders | MARKET order placed successfully | orderId=4729301823 status=FILLED
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing env var | Prints guidance, exits with code 1 |
| Invalid side / type | `validate_all()` raises `ValueError`, prints message, no API call made |
| Price missing for LIMIT | Validation error before any network activity |
| API error (e.g. -1111) | `BinanceAPIError` caught, logged, printed, exit code 1 |
| Network timeout / refused | `requests` exception caught, logged, printed, exit code 1 |

---

## Assumptions

- **USDT-M Futures only** — the base URL is fixed to `https://testnet.binancefuture.com/fapi`
- `timeInForce` for LIMIT orders defaults to `GTC` (Good Till Cancelled); this is the standard testnet default
- Quantity and price precision must match the symbol's exchange filters (Binance returns `-1111` if not)
- The bot does **not** auto-adjust precision — if you hit `-1111`, check the symbol's `LOT_SIZE` and `PRICE_FILTER` via `GET /fapi/v1/exchangeInfo`
- Credentials are read from environment variables only (12-factor app principle)

---

## Dependencies

```
requests>=2.31.0   # HTTP client for REST API calls
colorama>=0.4.6    # Cross-platform ANSI colour support (graceful fallback if absent)
```

No `python-binance` dependency — all API interaction is implemented via direct REST calls with HMAC-SHA256 signing.
