from app.repositories.prediction_repository import PredictionRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.wrong_question_repository import WrongQuestionRepository
from app.services.knowledge_service import KnowledgeService


class StatsService:
    def __init__(self) -> None:
        self.knowledge_service = KnowledgeService()
        self.prediction_repository = PredictionRepository()
        self.question_repository = QuestionRepository()
        self.wrong_question_repository = WrongQuestionRepository()

    def overview(self) -> dict:
        wrong_question_stats = self.wrong_question_repository.stats()
        legacy_prediction_stats = self.prediction_repository.stats()
        return {
            "knowledge_point_count": self.knowledge_service.count_points(),
            "question_count": self.question_repository.count(),
            "classification_count": int(
                wrong_question_stats.get("classification_count") or 0
            ),
            "avg_elapsed_ms": round(
                float(wrong_question_stats.get("avg_elapsed_ms") or 0), 2
            ),
            "cache_hit_count": int(wrong_question_stats.get("cache_hit_count") or 0),
            "latest_classification_at": wrong_question_stats.get(
                "latest_classification_at"
            ),
            "prediction_count": int(legacy_prediction_stats.get("prediction_count") or 0),
            "latest_prediction_at": legacy_prediction_stats.get("latest_prediction_at"),
        }
