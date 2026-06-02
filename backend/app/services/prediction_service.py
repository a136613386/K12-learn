import hashlib
import time

from app.cache.redis_client import get_json, set_json
from app.config import get_settings
from app.ml.predictor import get_predictor
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.prediction_repository import PredictionRepository


class PredictionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.knowledge_repository = KnowledgeRepository()
        self.prediction_repository = PredictionRepository()

    def predict(self, text: str) -> dict:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache_key = f"predict:knowledge_point:v1:{text_hash}"
        start = time.perf_counter()

        cached = get_json(cache_key)
        if cached:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            cached["elapsed_ms"] = elapsed_ms
            cached["cache_hit"] = True
            self._write_prediction_log(text_hash, text, cached, elapsed_ms, True)
            return cached

        prediction = get_predictor().predict(text)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        knowledge_point = self.knowledge_repository.get_by_id(prediction.label_id) or {}
        result = {
            "knowledge_point_id": prediction.label_id,
            "knowledge_point_name": knowledge_point.get("name", "未知知识点"),
            "confidence": prediction.confidence,
            "elapsed_ms": elapsed_ms,
            "cache_hit": False,
            "importance": knowledge_point.get("importance"),
            "difficulty": knowledge_point.get("difficulty"),
            "core_requirement": knowledge_point.get("core_requirement"),
        }

        cache_value = {key: value for key, value in result.items() if key != "elapsed_ms"}
        set_json(cache_key, cache_value, self.settings.redis_ttl_seconds)
        self._write_prediction_log(text_hash, text, result, elapsed_ms, False)
        return result

    def _write_prediction_log(
        self,
        text_hash: str,
        text: str,
        result: dict,
        elapsed_ms: float,
        cache_hit: bool,
    ) -> None:
        self.prediction_repository.create(
            text_hash=text_hash,
            input_text=text,
            predicted_label_id=int(result["knowledge_point_id"]),
            confidence=float(result["confidence"]),
            elapsed_ms=elapsed_ms,
            cache_hit=cache_hit,
        )
