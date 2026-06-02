import json
import logging
from typing import Any

from app.config import get_settings

try:
    import redis
except ImportError:  # pragma: no cover - 依赖未安装时走降级路径
    redis = None


logger = logging.getLogger(__name__)
_client = None


def get_redis_client():
    global _client
    if _client is not None:
        return _client
    if redis is None:
        raise RuntimeError("redis package is not installed")

    settings = get_settings()
    _client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=settings.redis_db,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    return _client


def check_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception:
        return False


def get_json(key: str) -> dict[str, Any] | None:
    try:
        raw_value = get_redis_client().get(key)
        if not raw_value:
            return None
        return json.loads(raw_value)
    except Exception as exc:
        # Redis 只是加速层，失败时不能阻断模型预测主流程。
        logger.warning("Redis 读取失败，已跳过缓存: %s", exc)
        return None


def set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    try:
        get_redis_client().setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
    except Exception as exc:
        # 缓存写入失败不影响接口结果，日志保留给后续排查连接或权限问题。
        logger.warning("Redis 写入失败，已跳过缓存: %s", exc)
