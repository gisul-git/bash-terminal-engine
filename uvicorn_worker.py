from __future__ import annotations

from uvicorn.workers import UvicornWorker


class ProductionUvicornWorker(UvicornWorker):
    """Custom Uvicorn worker with long-running session support (120 minutes)"""
    CONFIG_KWARGS = {
        "ws_ping_interval": 30,  # Send WebSocket ping every 30 seconds
        "ws_ping_timeout": 300,  # 5 minutes timeout for ping response
        "timeout_keep_alive": 300,  # Keep connection alive for 5 minutes
    }
