from app.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeService:
    def __init__(self) -> None:
        self.repository = KnowledgeRepository()

    def list_points(self) -> list[dict]:
        return self.repository.list_all()

    def count_points(self) -> int:
        return len(self.list_points())
