"""
Gunicorn configuration for TruthLens Backend.
Uses uvicorn workers for async ASGI support.
"""

import multiprocessing
import os

# ─── Server Socket ───
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# ─── Workers ───
# Rule of thumb: 2 * CPU + 1, but capped at 4 for ML workloads
# (each worker loads the model into memory)
_cpu_count = multiprocessing.cpu_count()
workers = min(2 * _cpu_count + 1, int(os.getenv("GUNICORN_WORKERS", 4)))
worker_class = "uvicorn.workers.UvicornWorker"

# ─── Timeouts ───
timeout = 120  # ML inference can take time
graceful_timeout = 30
keepalive = 5

# ─── Logging ───
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ─── Process Naming ───
proc_name = "truthlens-api"

# ─── Security ───
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# ─── Preload ───
# Disabled: each worker loads its own model copy to avoid shared-memory issues
preload_app = False
