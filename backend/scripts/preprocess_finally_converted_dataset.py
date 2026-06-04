import csv
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_DIR / "data" / "raw" / "finally_converted_tmp.csv"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
CLASS_PATH = PROCESSED_DIR / "class.txt"
TRAIN_PATH = PROCESSED_DIR / "train.txt"
DEV_PATH = PROCESSED_DIR / "dev.txt"
TEST_PATH = PROCESSED_DIR / "test.txt"

EXPECTED_CLASS_COUNT = 15
RANDOM_SEED = 20260603


@dataclass(frozen=True)
class Sample:
    text: str
    label_id: int


class PreprocessError(RuntimeError):
    pass


def normalize_space(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_prefix(value: Any, prefix: str) -> str:
    text = normalize_space(value)
    return re.sub(rf"^{prefix}[:：\s]*", "", text).strip()


def load_classes() -> list[str]:
    labels = [line.strip() for line in CLASS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(labels) != EXPECTED_CLASS_COUNT:
        raise PreprocessError(f"class.txt 必须包含 {EXPECTED_CLASS_COUNT} 个分类，当前为 {len(labels)}")
    return labels


def normalize_label(value: Any, label_count: int) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        label_id = int(float(str(value).strip()))
    except ValueError:
        return None
    if 0 <= label_id < label_count:
        return label_id
    return None


def build_training_text(question: Any, option: Any) -> str:
    stem = strip_prefix(question, "题干")
    options = strip_prefix(option, "选项")
    if not stem:
        return ""
    if options:
        return normalize_space(f"题干：{stem} 选项：{options}")
    return normalize_space(f"题干：{stem}")


def load_samples(labels: list[str]) -> tuple[list[Sample], Counter]:
    if not RAW_PATH.exists():
        raise PreprocessError(f"源文件不存在: {RAW_PATH}")

    filtered: Counter = Counter()
    samples: list[Sample] = []
    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"question", "option", "knowledge_points_id"}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise PreprocessError(f"CSV 缺少必需字段: {', '.join(missing)}")

        for row in reader:
            label_id = normalize_label(row.get("knowledge_points_id"), len(labels))
            if label_id is None:
                filtered["invalid_label"] += 1
                continue

            text = build_training_text(row.get("question"), row.get("option"))
            if not text:
                filtered["empty_text"] += 1
                continue

            samples.append(Sample(text=text, label_id=label_id))

    return samples, filtered


def deduplicate(samples: list[Sample], filtered: Counter) -> list[Sample]:
    seen = set()
    unique = []
    for sample in samples:
        key = (re.sub(r"\s+", "", sample.text).lower(), sample.label_id)
        if key in seen:
            filtered["duplicate"] += 1
            continue
        seen.add(key)
        unique.append(sample)
    return unique


def split_samples(samples: list[Sample]) -> dict[str, list[Sample]]:
    grouped: dict[int, list[Sample]] = defaultdict(list)
    for sample in samples:
        grouped[sample.label_id].append(sample)

    rng = random.Random(RANDOM_SEED)
    splits = {"train": [], "dev": [], "test": []}
    for label_id in sorted(grouped):
        rows = grouped[label_id]
        rng.shuffle(rows)
        total = len(rows)
        dev_count = max(1, round(total * 0.1))
        test_count = max(1, round(total * 0.1))
        train_count = total - dev_count - test_count
        if train_count <= 0:
            train_count = 1
            if test_count > 0:
                test_count -= 1
            elif dev_count > 0:
                dev_count -= 1

        splits["dev"].extend(rows[:dev_count])
        splits["test"].extend(rows[dev_count : dev_count + test_count])
        splits["train"].extend(rows[dev_count + test_count : dev_count + test_count + train_count])

    for rows in splits.values():
        rng.shuffle(rows)
    return splits


def write_split(path: Path, samples: list[Sample]) -> None:
    path.write_text(
        "\n".join(f"{sample.text}\t{sample.label_id}" for sample in samples) + "\n",
        encoding="utf-8",
    )


def distribution(samples: list[Sample]) -> dict[int, int]:
    return dict(sorted(Counter(sample.label_id for sample in samples).items()))


def main() -> int:
    try:
        class_before = CLASS_PATH.read_text(encoding="utf-8")
        labels = load_classes()
        samples, filtered = load_samples(labels)
        samples = deduplicate(samples, filtered)
        if not samples:
            raise PreprocessError("清洗后没有可用样本")

        splits = split_samples(samples)
        write_split(TRAIN_PATH, splits["train"])
        write_split(DEV_PATH, splits["dev"])
        write_split(TEST_PATH, splits["test"])

        class_after = CLASS_PATH.read_text(encoding="utf-8")
        if class_before != class_after:
            raise PreprocessError("class.txt 在处理过程中发生变化")

        print(f"finally_converted_tmp 数据集生成完成: train={len(splits['train'])}, dev={len(splits['dev'])}, test={len(splits['test'])}")
        print(f"过滤统计: {dict(filtered)}")
        print(f"全量分布: {distribution(samples)}")
        return 0
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
