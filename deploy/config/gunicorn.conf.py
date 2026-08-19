"""Gunicorn 生产配置（针对 2C4G 优化）。

- workers=2：2 核服务器建议 2 个 uvicorn worker（勿用 2*CPU+1 公式，4G 内存扛不住）
- 仅监听 127.0.0.1，对外统一由 Nginx 反向代理
- max_requests 防止内存泄漏累积（uvicorn 无进程复用，定期回收）
"""

import multiprocessing  # noqa: F401  # 保留用于参考 CPU 核数

# --- 监听 ---
bind = "127.0.0.1:8000"

# --- worker ---
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
threads = 1

# --- 超时（LLM 调用可能较慢，需大于 llm_timeout_seconds）---
timeout = 120
graceful_timeout = 30
keepalive = 5

# --- 内存回收 ---
max_requests = 1000
max_requests_jitter = 100

# --- 日志 ---
accesslog = "/home/aidoc/cacch-ai-platform/logs/gunicorn-access.log"
errorlog = "/home/aidoc/cacch-ai-platform/logs/gunicorn-error.log"
loglevel = "info"
