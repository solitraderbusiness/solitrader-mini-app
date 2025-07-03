# tg-trade-suite

Minimal setup for a Telegram trading suite with a PTB bot, FastAPI backend and React WebApps.

## Development

1. Copy `.env.example` to `.env` and fill in the secrets.
2. Install Python deps: `pip install -r requirements.txt`.
3. Install Node deps inside `webapp/tutorials`: `cd webapp/tutorials && npm install`.
4. Start services with Docker Compose:

```bash
docker-compose up --build
```

Access API at `https://localhost:443/ping` (via Caddy reverse proxy) and the tutorials WebApp at `https://localhost:443/tutorials`.
