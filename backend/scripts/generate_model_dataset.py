import csv
from collections import Counter
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.ml.data_blueprints import build_model_dataset_rows  # noqa: E402


def main(per_label: int = 100) -> int:
    output_path = PROJECT_DIR / "data" / "raw" / "model_dataset.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_model_dataset_rows(per_label)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "label_id", "label_name", "source"])
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["label_id"] for row in rows)
    report_path = PROJECT_DIR / "reports" / "model_dataset_distribution.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(f"label_id={label_id}: {count}" for label_id, count in sorted(counts.items())),
        encoding="utf-8",
    )
    print(f"????????: {output_path}")
    print(f"????: {len(rows)}??????: {min(counts.values())}")
    print(f"????: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
