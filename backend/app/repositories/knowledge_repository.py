from app.db import db_cursor
from app.ml.labels import KNOWLEDGE_POINT_BY_ID, KNOWLEDGE_POINTS


class KnowledgeRepository:
    def list_all(self) -> list[dict]:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, importance, difficulty, core_requirement, sort_order
                    FROM knowledge_points
                    ORDER BY sort_order ASC
                    """
                )
                rows = cursor.fetchall()
                return rows or KNOWLEDGE_POINTS
        except Exception:
            return KNOWLEDGE_POINTS

    def get_by_id(self, knowledge_point_id: int) -> dict | None:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, importance, difficulty, core_requirement, sort_order
                    FROM knowledge_points
                    WHERE id = %s
                    """,
                    (knowledge_point_id,),
                )
                row = cursor.fetchone()
                return row or KNOWLEDGE_POINT_BY_ID.get(knowledge_point_id)
        except Exception:
            return KNOWLEDGE_POINT_BY_ID.get(knowledge_point_id)
