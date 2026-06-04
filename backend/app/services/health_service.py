from app.cache.redis_client import check_redis
from app.db import check_mysql
from app.ml.predictor import get_predictor


class HealthService:
    def status(self) -> dict:
        mysql_connected = check_mysql()
        redis_connected = check_redis()
        predictor = get_predictor()
        model_loaded = predictor.model_loaded
        return {
            "status": "ok" if mysql_connected else "degraded",
            "model_loaded": model_loaded,
            "model_status": predictor.model_status,
            "model_load_error": predictor.load_error,
            "bert_loaded": predictor.bert_loaded,
            "bert_load_error": predictor.bert_load_error,
            "fasttext_loaded": predictor.fasttext_loaded,
            "fasttext_load_error": predictor.fasttext_load_error,
            "bert_confidence_threshold": predictor.settings.bert_confidence_threshold,
            "mysql_connected": mysql_connected,
            "redis_connected": redis_connected,
        }
