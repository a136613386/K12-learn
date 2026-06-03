import hashlib
import time

from app.cache.redis_client import get_json, set_json
from app.config import get_settings
from app.ml.predictor import get_predictor
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.wrong_question_repository import WrongQuestionRepository


class WrongQuestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.knowledge_repository = KnowledgeRepository()
        self.question_repository = QuestionRepository()
        self.wrong_question_repository = WrongQuestionRepository()

    def classify_and_recommend(self, text: str, limit: int = 5) -> dict:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache_key = f"wrong_question:classify_recommend:v2:{text_hash}:{limit}"
        start = time.perf_counter()

        cached = get_json(cache_key)
        if cached:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            result = {**cached, "elapsed_ms": elapsed_ms, "cache_hit": True}
            self._write_log(text_hash, text, result)
            return result

        prediction = get_predictor().predict(text)
        knowledge_point = self.knowledge_repository.get_by_id(prediction.label_id) or {}
        questions = self.question_repository.recommend_by_label(prediction.label_id, limit)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        result = {
            "classification": {
                "knowledge_point_id": prediction.label_id,
                "knowledge_point_name": knowledge_point.get("name", "Unknown knowledge point"),
                "confidence": prediction.confidence,
                "model_status": prediction.model_status,
                "importance": knowledge_point.get("importance"),
                "difficulty": knowledge_point.get("difficulty"),
                "core_requirement": knowledge_point.get("core_requirement"),
            },
            "recommended_questions": [self._serialize_question(item) for item in questions],
            "recommendation_count": len(questions),
            "elapsed_ms": elapsed_ms,
            "cache_hit": False,
        }

        cache_value = {
            key: value
            for key, value in result.items()
            if key not in {"elapsed_ms", "cache_hit"}
        }
        set_json(cache_key, cache_value, self.settings.redis_ttl_seconds)
        self._write_log(text_hash, text, result)
        return result

    def _serialize_question(self, item: dict) -> dict:
        return {
            "id": item.get("id"),
            "stem": item.get("stem"),
            "options": item.get("options"),
            "answer": item.get("answer"),
            "analysis": item.get("analysis"),
            "difficulty": item.get("difficulty"),
        }

    def _write_log(self, text_hash: str, text: str, result: dict) -> None:
        classification = result["classification"]
        question_ids = [
            int(item["id"])
            for item in result.get("recommended_questions", [])
            if item.get("id") is not None
        ]
        self.wrong_question_repository.create(
            text_hash=text_hash,
            input_text=text,
            predicted_label_id=int(classification["knowledge_point_id"]),
            confidence=float(classification["confidence"]),
            recommended_question_ids=question_ids,
            recommendation_count=int(result.get("recommendation_count") or 0),
            elapsed_ms=float(result.get("elapsed_ms") or 0),
            cache_hit=bool(result.get("cache_hit")),
        )
