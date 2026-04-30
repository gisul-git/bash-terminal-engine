from __future__ import annotations

import multiprocessing
import os


bind = "0.0.0.0:4041"
worker_class = "uvicorn_worker.ProductionUvicornWorker"
workers = int(os.getenv("WEB_CONCURRENCY", (multiprocessing.cpu_count() * 2) + 1))
timeout = 3600
keepalive = 120
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "warning")
