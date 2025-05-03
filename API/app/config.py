from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_title: str = "Code Rush 2025"
    api_version: str = "1.0.0"
    database_name: str = "mydatabase.db"
    secret_key: str = "your-secret-key-here"  
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_origins: list = [
        "http://localhost",
        "http://localhost:5173",
    ]
    
    
    class Config:
        env_file = ".env"

settings = Settings()