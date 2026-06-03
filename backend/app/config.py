from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"


def _load_env_file() -> None:
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return

    # 只在环境变量不存在时写入，避免覆盖命令行或系统中显式设置的配置。
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _bert_pretrained_path() -> Path:
    configured = os.getenv("BERT_PRETRAINED_PATH")
    if configured:
        configured_path = Path(configured)
        if not configured_path.is_absolute():
            configured_path = PROJECT_DIR / configured_path
        return configured_path

    return PROJECT_DIR / "backend/models/bert-base-chinese"


@dataclass(frozen=True)
class Settings:
    flask_host: str
    flask_port: int
    flask_debug: bool
    cors_origins: list[str]
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    redis_host: str
    redis_port: int
    redis_password: str | None
    redis_db: int
    redis_ttl_seconds: int
    model_path: Path
    bert_pretrained_path: Path
    class_path: Path
    data_dir: Path


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is not None:
        return _settings

    _load_env_file()
    cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    _settings = Settings(
        flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
        flask_port=_int_env("FLASK_PORT", 8000),
        flask_debug=_bool_env("FLASK_DEBUG", True),
        cors_origins=[item.strip() for item in cors.split(",") if item.strip()],
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=_int_env("DB_PORT", 3306),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", "123456"),
        db_name=os.getenv("DB_NAME", "k12-learn"),
        redis_host=os.getenv("REDIS_HOST", "127.0.0.1"),
        redis_port=_int_env("REDIS_PORT", 6379),
        redis_password=os.getenv("REDIS_PASSWORD") or None,
        redis_db=_int_env("REDIS_DB", 0),
        redis_ttl_seconds=_int_env("REDIS_TTL_SECONDS", 86400),
        model_path=PROJECT_DIR / os.getenv("MODEL_PATH", "backend/models/knowledge_bert"),
        bert_pretrained_path=_bert_pretrained_path(),
        class_path=PROJECT_DIR / os.getenv("CLASS_PATH", "data/processed/class.txt"),
        data_dir=PROJECT_DIR / os.getenv("DATA_DIR", "data/processed"),
    )
    return _settings
