import csv
import random
import re
from collections import Counter
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.ml.labels import KNOWLEDGE_POINTS  # noqa: E402


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def load_rows(path: Path) -> list[tuple[str, int]]:
    valid_labels = {item["id"] for item in KNOWLEDGE_POINTS}
    rows = []
    seen = set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"text", "label_id", "label_name", "source"}
        if not required.issubset(reader.fieldnames or set()):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"CSV ????: {sorted(missing)}")
        for line_no, row in enumerate(reader, start=2):
            text = normalize_text(row.get("text", ""))
            if not text:
                raise ValueError(f"? {line_no} ?????")
            label_id = int(row["label_id"])
            if label_id not in valid_labels:
                raise ValueError(f"? {line_no} ?????: {label_id}")
            key = (text, label_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append(key)
    return rows


def write_split(path: Path, rows: list[tuple[str, int]]) -> None:
    path.write_text("\n".join(f"{text}\t{label_id}" for text, label_id in rows) + "\n", encoding="utf-8")


def main() -> int:
    source_path = PROJECT_DIR / "data" / "raw" / "model_dataset.csv"
    if not source_path.exists():
        raise FileNotFoundError(f"??????: {source_path}")
    rows = load_rows(source_path)
    counts = Counter(label_id for _text, label_id in rows)
    if min(counts.values()) < 100:
        raise ValueError(f"????????? 100 ?????? {min(counts.values())} ?")

    rng = random.Random(20260602)
    by_label: dict[int, list[tuple[str, int]]] = {}
    for row in rows:
        by_label.setdefault(row[1], []).append(row)

    train_rows, dev_rows, test_rows = [], [], []
    for label_rows in by_label.values():
        rng.shuffle(label_rows)
        total = len(label_rows)
        dev_size = max(1, total // 10)
        test_size = max(1, total // 10)
        dev_rows.extend(label_rows[:dev_size])
        test_rows.extend(label_rows[dev_size : dev_size + test_size])
        train_rows.extend(label_rows[dev_size + test_size :])

    output_dir = PROJECT_DIR / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_split(output_dir / "train.txt", train_rows)
    write_split(output_dir / "dev.txt", dev_rows)
    write_split(output_dir / "test.txt", test_rows)
    (output_dir / "class.txt").write_text(
        "\n".join(item["name"] for item in KNOWLEDGE_POINTS) + "\n", encoding="utf-8"
    )

    report_path = PROJECT_DIR / "reports" / "preprocess_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        f"source={source_path}\nrows={len(rows)}\ntrain={len(train_rows)}\ndev={len(dev_rows)}\ntest={len(test_rows)}\n",
        encoding="utf-8",
    )
    print(f"?????: train={len(train_rows)}, dev={len(dev_rows)}, test={len(test_rows)}")
    print(f"??: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
