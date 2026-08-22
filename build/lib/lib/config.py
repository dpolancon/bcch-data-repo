"""
Purpose:  Environment-backed settings (BCCh API credentials, default date
          bounds), loaded from secrets/.env.
Task:     BCCh data pipeline infrastructure
Inputs:   secrets/.env -- BCCH_TOKEN (preferred), or
          BCCH_USER + BCCH_PASSWORD
Outputs:  n/a (module-level `settings` singleton, or None if unset)
Created:  2026-07-06
Updated:  2026-08-21
Owner:    dpolancon
"""

import os
from datetime import date
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from lib.paths import ENV_FILE as SECRETS_ENV_FILE
from lib.paths import LEGACY_ENV_FILE

# Credentials live in secrets/.env. A repo-root .env is still honoured so an
# existing checkout keeps working after the move. Real environment variables
# take precedence over both, since load_dotenv does not override them.
ENV_FILE = SECRETS_ENV_FILE if SECRETS_ENV_FILE.exists() else LEGACY_ENV_FILE
load_dotenv(ENV_FILE)

# Credential values that mean "the template was never filled in".
PLACEHOLDER_MARKERS = ("your_email@example.com", "example.com", "your_api_password")


class Settings(BaseSettings):
    # All three are optional so the module imports cleanly with no credentials.
    # Validity is decided by has_credentials(), which accepts either scheme:
    # an API Key token (BCCh's recommended REST auth) or the legacy user pair.
    bcch_token: Optional[str] = Field(default=None, validation_alias="BCCH_TOKEN")
    bcch_user: Optional[str] = Field(default=None, validation_alias="BCCH_USER")
    bcch_password: Optional[str] = Field(default=None, validation_alias="BCCH_PASSWORD")

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
    warnings.warn(f"Failed to load BCCh settings. Set BCCH_TOKEN (or BCCH_USER and BCCH_PASSWORD) in your environment: {e}")


def _is_placeholder(value: Optional[str]) -> bool:
    if not value or not value.strip():
        return True
    return any(marker in value.lower() for marker in PLACEHOLDER_MARKERS)


def credentials_are_placeholders() -> bool:
    """True when no usable credential is configured.

    Either scheme suffices: a token on its own, or a complete user/password
    pair. Placeholder values from .env.example count as absent.
    """
    if settings is None:
        return True
    if not _is_placeholder(settings.bcch_token):
        return False
    return _is_placeholder(settings.bcch_user) or _is_placeholder(settings.bcch_password)


def require_real_credentials() -> None:
    """Abort loudly when credentials are missing or unfilled.

    Fetch stages call this before touching the API. Failing here is deliberate:
    the alternative that used to exist -- silently generating synthetic data --
    produced files indistinguishable from real ones at a glance.
    """
    if credentials_are_placeholders():
        raise RuntimeError(
            "BCCh API credentials are missing or still set to the example "
            "placeholders. Copy secrets/.env.example to secrets/.env and set "
            "BCCH_TOKEN (get an API Key token from 'Mi Cuenta' > 'Apikey Token' "
            "at si3.bcentral.cl), or set BCCH_USER and BCCH_PASSWORD. "
            "See secrets/README.md. This pipeline will not fabricate data as a "
            "fallback."
        )
