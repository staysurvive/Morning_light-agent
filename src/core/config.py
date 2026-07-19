# 读取环境变量中的配置
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "MyApp"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "17bfb8d274f91b4bf09f55d0c2d086319c251859c7a0edf1aef823e4c3c5adea"

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "myapp"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    KNOWLEDGE_STORAGE_DIR: str = "data/knowledge"
    MAX_DOCUMENT_SIZE_MB: int = 20

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # 指定环境变量文件
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

# 保存到内存缓存中。以后直接获取。这是一种单例的实现
@lru_cache   # 把对象实例保存到内存缓存中
def get_settings() -> Settings:
    return Settings()
