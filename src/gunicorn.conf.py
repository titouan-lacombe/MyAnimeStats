from src.config import Config

# Static configuration
wsgi_app = "src.main:app"
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
reload_engine = "inotify"
capture_output = True

# Dynamic configuration
class ServerConfig(Config):
    reload: bool = False
    timeout: int = 120
    graceful_timeout: int = 120
    log_level: str = "info"
    workers: int = 1
    max_requests: int = 10000
    max_requests_jitter: int = 5000

server_config = ServerConfig.from_env()

reload = server_config.reload
timeout = server_config.timeout
graceful_timeout = server_config.graceful_timeout
loglevel = server_config.log_level
workers = server_config.workers
max_requests = server_config.max_requests
max_requests_jitter = server_config.max_requests_jitter
