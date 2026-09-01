from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH Memory Forensics API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database
    DATABASE_PATH: str = "./forensics.db"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"sqlite+aiosqlite:///{self.DATABASE_PATH}"

    @property
    def SYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"sqlite:///{self.DATABASE_PATH}"

    # Storage & Symbols
    STORAGE_DIR: str = "../storage"
    SYMBOLS_DIR: str = "../symbols"

    class Config:
        case_sensitive = True

settings = Settings()
