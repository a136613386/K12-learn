from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "processed"


def load_labels() -> list[str]:
    class_path = DATA_DIR / "class.txt"
    if not class_path.exists():
        raise FileNotFoundError(f"标签文件不存在: {class_path}")
    return [line.strip() for line in class_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_file(path: Path, label_count: int) -> int:
    errors = 0
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}")
        return 1

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            print(f"[ERROR] {path.name}:{line_no} 必须使用 tab 分隔文本和标签")
            errors += 1
            continue
        text, label_raw = parts
        if not text.strip():
            print(f"[ERROR] {path.name}:{line_no} 题目文本为空")
            errors += 1
        try:
            label = int(label_raw)
        except ValueError:
            print(f"[ERROR] {path.name}:{line_no} 标签不是整数: {label_raw}")
            errors += 1
            continue
        if label < 0 or label >= label_count:
            print(f"[ERROR] {path.name}:{line_no} 标签超出范围: {label}")
            errors += 1
    return errors


def main() -> int:
    labels = load_labels()
    total_errors = 0
    for file_name in ["train.txt", "dev.txt", "test.txt"]:
        total_errors += validate_file(DATA_DIR / file_name, len(labels))

    if total_errors:
        print(f"数据校验失败，共 {total_errors} 个问题")
        return 1
    print("数据校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
