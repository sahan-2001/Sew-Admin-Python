from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"
    DB_PORT: str = "3306"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "sew_admin"
    DATABASE_URL: str | None = None
    SECRET_KEY: str = "yG9O1T_w7D9M4YxRbkLqVJhN_kZ5fK2g8V0c3T7pXZo="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    @property
    def database_url(self) -> str | None:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.DB_PASSWORD:
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"mysql+pymysql://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
