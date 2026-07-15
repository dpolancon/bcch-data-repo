import os
from datetime import date
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

class Settings(BaseSettings):
    bcch_user: str = Field(..., validation_alias="BCCH_USER")
    bcch_password: str = Field(..., validation_alias="BCCH_PASSWORD")
    
    # Fallback start/end dates
    default_start_date: date = Field(default=date(1980, 1, 1))
    default_end_date: date = Field(default_factory=date.today)
    
    model_config = SettingsConfigDict(
        env_file=".env",
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
