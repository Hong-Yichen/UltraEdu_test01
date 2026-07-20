import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(INSTANCE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 50)) * 1024 * 1024
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProdConfig(Config):
    DEBUG = False


CONFIG_MAP = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}
