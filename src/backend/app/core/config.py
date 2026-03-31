import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Automatización Inteligente PQR"

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "pqr-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # SQL Server
    HOST: str = os.getenv("HOST", "localhost")
    PORT: str = os.getenv("PORT", "1433")
    DB: str = os.getenv("DB", "PQR_DB")
    USER: str = os.getenv("DB_USER", "sa")
    PASSWORD: str = os.getenv("PASSWORD", "")

    # CORS
    ALLOWED_ORIGINS: list = [
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    ]

    @property
    def db_config(self) -> dict:
        return {
            "host": self.HOST,
            "port": self.PORT,
            "dbname": self.DB,
            "user": self.USER,
            "password": self.PASSWORD,
        }


settings = Settings()
