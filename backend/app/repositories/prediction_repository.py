from app.db import db_cursor


class PredictionRepository:
    def create(
        self,
        *,
        text_hash: str,
        input_text: str,
        predicted_label_id: int,
        confidence: float,
        elapsed_ms: float,
        cache_hit: bool,
    ) -> None:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO prediction_logs
                        (text_hash, input_text, predicted_label_id, confidence, elapsed_ms, cache_hit)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        text_hash,
                        input_text,
                        predicted_label_id,
                        confidence,
                        elapsed_ms,
                        1 if cache_hit else 0,
                    ),
                )
        except Exception:
            # MVP 阶段数据库不可用时不阻断演示预测；生产环境应接入结构化日志和告警。
            return

    def recent(self, limit: int = 10) -> list[dict]:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.input_text,
                        p.predicted_label_id AS knowledge_point_id,
                        k.name AS knowledge_point_name,
                        p.confidence,
                        p.elapsed_ms,
                        p.cache_hit,
                        p.created_at
                    FROM prediction_logs p
                    LEFT JOIN knowledge_points k ON k.id = p.predicted_label_id
                    ORDER BY p.created_at DESC
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
                        COUNT(*) AS prediction_count,
                        COALESCE(AVG(elapsed_ms), 0) AS avg_elapsed_ms,
                        COALESCE(SUM(cache_hit), 0) AS cache_hit_count,
                        MAX(created_at) AS latest_prediction_at
                    FROM prediction_logs
                    """
                )
                row = cursor.fetchone() or {}
                if row.get("latest_prediction_at") is not None:
                    row["latest_prediction_at"] = row["latest_prediction_at"].isoformat(sep=" ")
                return row
        except Exception:
            return {
                "prediction_count": 0,
                "avg_elapsed_ms": 0,
                "cache_hit_count": 0,
                "latest_prediction_at": None,
            }
