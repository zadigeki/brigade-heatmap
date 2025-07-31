"""
Configuration file for Brigade Electronics API integration
"""
import os
from dataclasses import dataclass

@dataclass
class APIConfig:
    """Configuration for Brigade Electronics API"""
    base_url: str = "http://127.0.0.1:12056"
    username: str = "admin"
    password: str = "admin"  # Should be MD5 hashed
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5

@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_path: str = "devices.db"
    connection_timeout: int = 30

@dataclass
class SchedulerConfig:
    """Scheduler configuration"""
    update_interval_minutes: int = 10
    max_concurrent_tasks: int = 1

@dataclass
class AlarmConfig:
    """Alarm monitoring configuration"""
    update_interval_minutes: int = 5
    lookback_minutes: int = 10
    batch_size: int = 50
    cleanup_days: int = 30

# Environment variable overrides
API_CONFIG = APIConfig(
    base_url=os.getenv("BRIGADE_API_URL", "http://127.0.0.1:12056"),
    username=os.getenv("BRIGADE_USERNAME", "admin"),
    password=os.getenv("BRIGADE_PASSWORD", "admin"),
    timeout=int(os.getenv("BRIGADE_API_TIMEOUT", "30")),
    retry_attempts=int(os.getenv("BRIGADE_RETRY_ATTEMPTS", "3")),
    retry_delay=int(os.getenv("BRIGADE_RETRY_DELAY", "5"))
)

DATABASE_CONFIG = DatabaseConfig(
    db_path=os.getenv("DATABASE_PATH", "/app/data/devices.db"),
    connection_timeout=int(os.getenv("DB_TIMEOUT", "30"))
)

SCHEDULER_CONFIG = SchedulerConfig(
    update_interval_minutes=int(os.getenv("UPDATE_INTERVAL_MINUTES", "10")),
    max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "1"))
)

ALARM_CONFIG = AlarmConfig(
    update_interval_minutes=int(os.getenv("ALARM_UPDATE_INTERVAL_MINUTES", "5")),
    lookback_minutes=int(os.getenv("ALARM_LOOKBACK_MINUTES", "10")),
    batch_size=int(os.getenv("ALARM_BATCH_SIZE", "50")),
    cleanup_days=int(os.getenv("ALARM_CLEANUP_DAYS", "30"))
)