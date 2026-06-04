import json
import re
from collections import Counter
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.ml.fasttext_tokenizer import tokenize_text as runtime_tokenize_text  # noqa: E402

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
FASTTEXT_DIR = PROJECT_DIR / "data" / "fasttext"
REPORTS_DIR = PROJECT_DIR / "reports"

CLASS_PATH = PROCESSED_DIR / "class.txt"
REPORT_PATH = REPORTS_DIR / "fasttext_preprocess_report.json"
EXPECTED_CLASS_COUNT = 15
TOKENIZATION_MODE = "char_with_ascii_chunks"


class FastTextPreprocessError(RuntimeError):
    pass


def load_labels() -> list[str]:
    if not CLASS_PATH.exists():
        raise FastTextPreprocessError(f"class.txt 不存在: {CLASS_PATH}")
    labels = [line.strip() for line in CLASS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(labels) != EXPECTED_CLASS_COUNT:
        raise FastTextPreprocessError(f"class.txt 必须包含 {EXPECTED_CLASS_COUNT} 个分类，当前为 {len(labels)}")
    return labels


def tokenize_text(text: str) -> str:
    tokens: list[str] = []
    buffer: list[str] = []

    def flush_buffer() -> None:
        if buffer:
            tokens.append("".join(buffer))
            buffer.clear()

    for char in text.strip():
        if char.isspace():
            flush_buffer()
            continue
        if re.match(r"[A-Za-z0-9_+\-*/=<>^:.%]+", char):
            buffer.append(char)
            continue
        flush_buffer()
        if not re.match(r"[\u3000\s，。！？；：、“”‘’（）()\[\]{}《》,!?;\"']", char):
            tokens.append(char)

    flush_buffer()
    return " ".join(tokens)


def parse_processed_line(path: Path, line_no: int, raw_line: str, label_count: int) -> tuple[str, int]:
    line = raw_line.strip()
    if not line:
        raise FastTextPreprocessError(f"{path.name}:{line_no} 空行不允许进入 FastText 数据")
    parts = line.rsplit("\t", 1)
    if len(parts) != 2:
        raise FastTextPreprocessError(f"{path.name}:{line_no} 必须使用单个 tab 分隔文本和标签")
    text, label_raw = parts
    text = text.strip()
    if not text:
        raise FastTextPreprocessError(f"{path.name}:{line_no} 文本为空")
    try:
        label_id = int(label_raw)
    except ValueError as error:
        raise FastTextPreprocessError(f"{path.name}:{line_no} 标签不是整数: {label_raw}") from error
    if label_id < 0 or label_id >= label_count:
        raise FastTextPreprocessError(f"{path.name}:{line_no} 标签超出范围: {label_id}")
    return text, label_id


def convert_split(split_name: str, label_count: int) -> dict:
    input_path = PROCESSED_DIR / f"{split_name}.txt"
    output_path = FASTTEXT_DIR / f"{split_name}.txt"
    if not input_path.exists():
        raise FastTextPreprocessError(f"processed 文件不存在: {input_path}")

    rows = []
    distribution: Counter[int] = Counter()
    token_lengths = []
    for line_no, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        text, label_id = parse_processed_line(input_path, line_no, raw_line, label_count)
        tokenized = runtime_tokenize_text(text)
        if not tokenized:
            raise FastTextPreprocessError(f"{input_path.name}:{line_no} 分词后文本为空")
        rows.append(f"__label__{label_id} {tokenized}")
        distribution[label_id] += 1
        token_lengths.append(len(tokenized.split()))

    output_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "count": len(rows),
        "distribution": {str(label): count for label, count in sorted(distribution.items())},
        "avg_tokens": round(sum(token_lengths) / len(token_lengths), 2) if token_lengths else 0,
        "max_tokens": max(token_lengths) if token_lengths else 0,
    }


def main() -> int:
    try:
        class_before = CLASS_PATH.read_text(encoding="utf-8") if CLASS_PATH.exists() else ""
        labels = load_labels()
        FASTTEXT_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        splits = {
            split_name: convert_split(split_name, len(labels))
            for split_name in ["train", "dev", "test"]
        }

        class_after = CLASS_PATH.read_text(encoding="utf-8")
        if class_before != class_after:
            raise FastTextPreprocessError("class.txt 在 FastText 预处理过程中发生变化")

        report = {
            "tokenization": {
                "mode": TOKENIZATION_MODE,
                "description": "中文按字符切分，连续英文/数字/遗传符号保留为 token",
            },
            "class_file": {
                "path": str(CLASS_PATH),
                "count": len(labels),
                "labels": labels,
                "unchanged": True,
            },
            "splits": splits,
            "filtered": {},
        }
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            "FastText 数据预处理完成: "
            + ", ".join(f"{name}={info['count']}" for name, info in splits.items())
        )
        print(f"报告: {REPORT_PATH}")
        return 0
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
