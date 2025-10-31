from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    App settings loaded from environment (.env if present).
    - All datetimes are normalized to UTC internally.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Auth (Basic) ---
    BASIC_AUTH_USERNAME: str = "doctor"
    BASIC_AUTH_PASSWORD: str = "change-me"

    # --- App behavior ---
    BOOKING_SLOT_MINUTES: int = 30


settings = Settings()
