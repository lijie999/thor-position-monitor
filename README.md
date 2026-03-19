# Thor Position Monitor

Local real-time position monitoring dashboard for [Thor Trade Copier](https://thortradecopier.com).

![Dark theme trading dashboard](https://img.shields.io/badge/theme-dark-0d1117) ![Zero dependencies](https://img.shields.io/badge/dependencies-zero-green) ![License MIT](https://img.shields.io/badge/license-MIT-blue)

## Features

- Real-time positions, working orders, closed positions
- Net PnL summary across all accounts
- Connection status monitoring
- One-click flatten all / close single position / cancel order
- Historical trade statistics (win rate, profit factor, streaks)
- Auto-refresh (3s polling, configurable)
- Dark theme, single HTML file, zero dependencies

## Setup

1. Clone this repo
2. Copy config template and fill in your API credentials:

```bash
cp config.example.js config.js
```

3. Edit `config.js` with your Thor API key and secret:

```js
const CONFIG = {
  API_KEY: 'thor_abc123...',
  API_SECRET: 'thorsec_xyz789...',
  BASE_URL: '',              // empty when using server.js proxy
  REFRESH_INTERVAL: 3000,
};
```

4. Start the local server (includes CORS proxy):

```bash
node server.js
```

5. Open http://localhost:8080

> `server.js` serves static files and proxies `/api/*` requests to Thor's API, bypassing CORS restrictions. Zero npm dependencies required.

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/connections` | Account connection status |
| `GET /api/v1/positions/running` | Open positions |
| `GET /api/v1/positions/orders` | Working orders |
| `GET /api/v1/positions/closed` | Closed positions today |
| `GET /api/v1/risk/lockouts` | Locked accounts |
| `GET /api/v1/historical/trades/stats` | Trade statistics |
| `POST /api/v1/positions/flatten` | Flatten all positions |
| `POST /api/v1/positions/close` | Close specific position |
| `POST /api/v1/positions/cancel` | Cancel working order |

Rate limit: 100 requests/minute.

## Security

- `config.js` is in `.gitignore` — your API keys are never committed
- `config.example.js` is the template with placeholder values
- No data is sent to any third party — all requests go directly to Thor's API

## License

MIT
