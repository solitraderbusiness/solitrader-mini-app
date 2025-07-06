import logging, os

# Root level comes from env (default = INFO)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s  %(levelname)-7s %(name)s - %(message)s",
)

# Keep 3 × 5 MB per run-time log file inside /app/logs
from logging.handlers import RotatingFileHandler
fh = RotatingFileHandler(
    "/app/logs/bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s %(name)s - %(message)s"))
logging.getLogger().addHandler(fh)

# Silence very chatty libraries
for noisy in ("telegram", "telegram.ext", "httpx"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

