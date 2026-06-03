from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.db import db_cursor  # noqa: E402
from app.ml.data_blueprints import build_question_bank_rows  # noqa: E402


def main(per_label: int = 20) -> int:
    rows = build_question_bank_rows(per_label)
    with db_cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO questions (id, stem, options, answer, analysis, label_id, difficulty, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stem = VALUES(stem),
                options = VALUES(options),
                answer = VALUES(answer),
                analysis = VALUES(analysis),
                label_id = VALUES(label_id),
                difficulty = VALUES(difficulty),
                source = VALUES(source)
            """,
            [
                (
                    row["id"],
                    row["stem"],
                    row["options"],
                    row["answer"],
                    row["analysis"],
                    row["label_id"],
                    row["difficulty"],
                    row["source"],
                )
                for row in rows
            ],
        )
    print(f"????????: {len(rows)} ???{per_label} ?/???")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
