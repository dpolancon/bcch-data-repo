"""
Purpose:  Environment-backed settings (BCCh API credentials, default date
          bounds), loaded from the repo-root .env.
Task:     BCCh data pipeline infrastructure
Inputs:   <repo root>/.env -- BCCH_USER, BCCH_PASSWORD
Outputs:  n/a (module-level `settings` singleton, or None if unset)
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
"""

import os
from datetime import date
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from lib.paths import REPO_ROOT

# Anchor .env to the repo root so credentials resolve no matter the CWD.
ENV_FILE = REPO_ROOT / ".env"
load_dotenv(ENV_FILE)

# Credential values that mean "the template was never filled in".
PLACEHOLDER_MARKERS = ("your_email@example.com", "example.com", "your_api_password")


class Settings(BaseSettings):
    bcch_user: str = Field(..., validation_alias="BCCH_USER")
    bcch_password: str = Field(..., validation_alias="BCCH_PASSWORD")
    
    # Fallback start/end dates
    default_start_date: date = Field(default=date(1980, 1, 1))
    default_end_date: date = Field(default_factory=date.today)
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
try:
    settings = Settings()
except Exception as e:
    # Allow running if we are just loading module but raise warning/error when client is created
    settings = None
    import warnings
    warnings.warn(f"Failed to load BCCh settings. Ensure BCCH_USER and BCCH_PASSWORD are set in your environment: {e}")


def credentials_are_placeholders() -> bool:
    """True when .env still holds the template values from .env.example."""
    if settings is None:
        return True
    blob = f"{settings.bcch_user} {settings.bcch_password}".lower()
    return any(marker in blob for marker in PLACEHOLDER_MARKERS)


def require_real_credentials() -> None:
    """Abort loudly when credentials are missing or unfilled.

    Fetch stages call this before touching the API. Failing here is deliberate:
    the alternative that used to exist -- silently generating synthetic data --
    produced files indistinguishable from real ones at a glance.
    """
    if credentials_are_placeholders():
        raise RuntimeError(
            "BCCh API credentials are missing or still set to the .env.example "
            "placeholders. Copy .env.example to .env and fill in BCCH_USER and "
            "BCCH_PASSWORD. This pipeline will not fabricate data as a fallback."
        )
