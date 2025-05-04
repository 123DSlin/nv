"""
Configuration settings for the Network Verifier system.
"""

from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Batfish settings
    batfish_host: str = "localhost"
    batfish_port: int = 9997
    
    # Network configuration settings
    config_dir: str = "configs"
    snapshot_dir: str = "snapshots"
    
    # Verification settings
    default_timeout: int = 300  # seconds
    max_retries: int = 3
    
    # Output settings
    report_dir: str = "reports"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 