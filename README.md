# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on the **Binance Spot Testnet** (`testnet.binance.vision`).

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

### 1. Clone the repository

```bash
git clone https://github.com/SaiRupesh07/Binance-Futures-Testnet-Trading-Bot.git
cd Binance-Futures-Testnet-Trading-Bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Register on Binance Spot Testnet

1. Go to [https://testnet.binance.vision](https://testnet.binance.vision)
2. Click **"Log In with GitHub"**
3. Click **"Generate HMAC_SHA256 Key"**
4. Enter a description, make sure **TRADE** and **USER_DATA** are checked
5. Click **Generate** and copy both the **API Key** and **Secret Key**

> Note: The Binance Futures Testnet (`testnet.binancefuture.com`) may be geo-restricted in some regions (e.g. India). The Spot Testnet (`testnet.binance.vision`) provides equivalent functionality for testing order placement.

### 5. Create a `.env` file in the project root

```
BINANCE_TESTNET_API_KEY=your_api_key_here
BINANCE_TESTNET_API_SECRET=your_secret_here
```

> The bot reads credentials from the `.env` file automatically via `python-dotenv`. Never commit this file to Git.

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
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
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
  orderId      : 978428
  clientOrderId: KvYY4xUlLvLZQzdV2lJ9Bp
  status       : FILLED
  executedQty  : 0.00100000
  price        : 0.00000000
  type         : MARKET
  side         : BUY
  timeInForce  : GTC
────────────────────────────────────────────────────────────
✔ Order placed successfully!
```

### Place a LIMIT order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 98000
```

### Place a STOP_MARKET order (bonus)

```bash
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 70000
```

> Note: Stop price must be **below** the current market price for SELL stop orders.

### Increase log verbosity

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
2026-05-08 11:56:26 | INFO  | trading_bot.orders | Placing MARKET order | symbol=BTCUSDT side=BUY qty=0.001
2026-05-08 11:56:27 | INFO  | trading_bot.orders | MARKET order placed successfully | orderId=978428 status=FILLED
2026-05-08 11:57:09 | INFO  | trading_bot.orders | Placing LIMIT order | symbol=BTCUSDT side=SELL qty=0.001 price=98000 tif=GTC
2026-05-08 11:57:10 | INFO  | trading_bot.orders | LIMIT order placed successfully | orderId=978869 status=NEW
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing env var | Prints guidance, exits with code 1 |
| Invalid side / type | `validate_all()` raises `ValueError`, no API call made |
| Price missing for LIMIT | Validation error before any network activity |
| API error (e.g. -2015) | `BinanceAPIError` caught, logged, printed, exit code 1 |
| Network timeout | `requests` exception caught, logged, printed, exit code 1 |

---

## Assumptions

- Uses **Binance Spot Testnet** (`testnet.binance.vision`) with `/api/v3/` endpoints
- The Futures Testnet (`testnet.binancefuture.com`) is geo-restricted in India — Spot Testnet provides equivalent order-placement testing
- `timeInForce` for LIMIT orders defaults to `GTC` (Good Till Cancelled)
- STOP_MARKET orders are implemented as `STOP_LOSS_LIMIT` on the Spot testnet (Futures-only order type mapped to nearest equivalent)
- Stop price for SELL stop orders must be below current market price
- Credentials are loaded from `.env` file via `python-dotenv` (12-factor app principle)

---

## Dependencies

```
requests>=2.31.0      # HTTP client for REST API calls
colorama>=0.4.6       # Cross-platform ANSI colour support
python-dotenv>=1.0.0  # Load credentials from .env file
```

No `python-binance` dependency — all API interaction is implemented via direct REST calls with HMAC-SHA256 signing.
