import os
from dataclasses import dataclass


@dataclass
class Config:
    TRUSTED_HOSTS = ["*"]
    ALLOW_SITE = ["*"]
    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = True
    DEBUG: bool = True
    DB_URL: str = os.environ.get("DB_URL")
    print(os.environ.items())


@dataclass
class DevConfig(Config):
    ...


@dataclass
class ProdConfig(Config):
    DEBUG: bool = False



def env():
    """
    Load Env
    """
    config = dict(dev=DevConfig, prod=ProdConfig)
    return config[os.environ.get("API_ENV", "dev")]()


