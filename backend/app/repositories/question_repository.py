from app.db import db_cursor
from app.ml.sample_questions import SAMPLE_QUESTIONS


class QuestionRepository:
    def recommend_by_label(self, label_id: int, limit: int = 5) -> list[dict]:
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, stem, options, answer, analysis, label_id, difficulty
                    FROM questions
                    WHERE label_id = %s
                      AND stem IS NOT NULL
                      AND answer IS NOT NULL
                    ORDER BY COALESCE(difficulty, 3) ASC, id DESC
                    LIMIT %s
                    """,
                    (label_id, limit),
                )
                rows = cursor.fetchall()
                if rows:
                    return rows
        except Exception:
            pass

        return [
            item.copy()
            for item in SAMPLE_QUESTIONS
            if item["label_id"] == label_id
        ][:limit]

    def count(self) -> int:
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS question_count FROM questions")
                row = cursor.fetchone() or {}
                count = int(row.get("question_count") or 0)
                return count or len(SAMPLE_QUESTIONS)
        except Exception:
            return len(SAMPLE_QUESTIONS)
