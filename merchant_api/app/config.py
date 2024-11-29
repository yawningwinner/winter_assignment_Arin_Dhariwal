from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://merchant_user@localhost:5432/merchant_db"
    # API settings
    API_V1_STR: str = "/api/Arinki"
    PROJECT_NAME: str = "Merchant API"
    class Config:
        env_file = ".env"

settings = Settings() 