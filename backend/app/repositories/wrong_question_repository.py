import json

from app.db import db_cursor


class WrongQuestionRepository:
    def create(
        self,
        *,
        text_hash: str,
        input_text: str,
        predicted_label_id: int,
        confidence: float,
        recommended_question_ids: list[int],
        recommendation_count: int,
        elapsed_ms: float,
        cache_hit: bool,
    ) -> None:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO wrong_question_logs
                        (
                            text_hash,
                            input_text,
                            predicted_label_id,
                            confidence,
                            recommended_question_ids,
                            recommendation_count,
                            elapsed_ms,
                            cache_hit
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        text_hash,
                        input_text,
                        predicted_label_id,
                        confidence,
                        json.dumps(recommended_question_ids, ensure_ascii=False),
                        recommendation_count,
                        elapsed_ms,
                        1 if cache_hit else 0,
                    ),
                )
        except Exception:
            # MVP ??????????????????????
            return

    def recent(self, limit: int = 10) -> list[dict]:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        w.id,
                        w.input_text,
                        w.predicted_label_id AS knowledge_point_id,
                        k.name AS knowledge_point_name,
                        w.confidence,
                        w.recommendation_count,
                        w.elapsed_ms,
                        w.cache_hit,
                        w.created_at
                    FROM wrong_question_logs w
                    LEFT JOIN knowledge_points k ON k.id = w.predicted_label_id
                    ORDER BY w.created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                for row in rows:
                    row["cache_hit"] = bool(row.get("cache_hit"))
                    if row.get("created_at") is not None:
                        row["created_at"] = row["created_at"].isoformat(sep=" ")
                return rows
        except Exception:
            return []

    def stats(self) -> dict:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS classification_count,
                        COALESCE(AVG(elapsed_ms), 0) AS avg_elapsed_ms,
                        COALESCE(SUM(cache_hit), 0) AS cache_hit_count,
                        MAX(created_at) AS latest_classification_at
                    FROM wrong_question_logs
                    """
                )
                row = cursor.fetchone() or {}
                if row.get("latest_classification_at") is not None:
                    row["latest_classification_at"] = row[
                        "latest_classification_at"
                    ].isoformat(sep=" ")
                return row
        except Exception:
            return {
                "classification_count": 0,
                "avg_elapsed_ms": 0,
                "cache_hit_count": 0,
                "latest_classification_at": None,
            }
