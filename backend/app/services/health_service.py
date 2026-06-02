from app.cache.redis_client import check_redis
from app.db import check_mysql
from app.ml.predictor import get_predictor


class HealthService:
    def status(self) -> dict:
        mysql_connected = check_mysql()
        redis_connected = check_redis()
        model_loaded = get_predictor().model_loaded
        return {
            "status": "ok" if mysql_connected else "degraded",
            "model_loaded": model_loaded,
            "mysql_connected": mysql_connected,
            "redis_connected": redis_connected,
        }
