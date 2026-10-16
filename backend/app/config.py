from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ExpenseTracker API"
    database_url: str = "postgresql+psycopg://expense_tracker:expense_tracker@localhost:5432/expense_tracker"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
