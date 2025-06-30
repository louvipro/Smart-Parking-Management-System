from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    
    # Development
    DEV_MODE: bool = Field(default=True, description="Enable debug mode")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./parking.db", description="Database connection URL")
    ASYNC_DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./parking.db", description="Async database URL")
    
    
    
    # Streamlit
    STREAMLIT_PORT: int = Field(default=8501, description="Streamlit port")
    
    # Parking Configuration
    HOURLY_RATE: float = Field(default=5.0, description="Hourly parking rate")
    PARKING_FLOORS: int = Field(default=3, description="Number of parking floors")
    SPOTS_PER_FLOOR: int = Field(default=20, description="Spots per floor")
    



# Create settings instance
settings = Settings()