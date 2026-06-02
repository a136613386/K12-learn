from app.repositories.prediction_repository import PredictionRepository
from app.services.knowledge_service import KnowledgeService


class StatsService:
    def __init__(self) -> None:
        self.knowledge_service = KnowledgeService()
        self.prediction_repository = PredictionRepository()

    def overview(self) -> dict:
        stats = self.prediction_repository.stats()
        return {
            "knowledge_point_count": self.knowledge_service.count_points(),
            "prediction_count": int(stats.get("prediction_count") or 0),
            "avg_elapsed_ms": round(float(stats.get("avg_elapsed_ms") or 0), 2),
            "cache_hit_count": int(stats.get("cache_hit_count") or 0),
            "latest_prediction_at": stats.get("latest_prediction_at"),
        }
