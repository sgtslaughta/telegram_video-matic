from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """App config from env vars + sensible defaults."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str = "sqlite+aiosqlite:////data/tvm.sqlite"

    # Secrets (REQUIRED at startup)
    tvm_secret_key: str

    # Tunables (persist in DB as Setting, but env provides defaults)
    poll_interval_sec: int = 300
    retention_days: int = 90
    retention_disk_pct: int = 80
    max_concurrent_downloads: int = 3
    theme: str = "auto"

    # FastAPI
    debug: bool = False
    app_password: Optional[str] = None

    def __init__(self, **data):
        """Validate TVM_SECRET_KEY is set before allowing init."""
        super().__init__(**data)
        if not self.tvm_secret_key or self.tvm_secret_key.strip() == "":
            raise ValueError(
                "TVM_SECRET_KEY environment variable must be set and non-empty. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
