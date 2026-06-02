import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.config import get_settings  # noqa: E402
from app.ml.predictor import get_predictor  # noqa: E402
from scripts.validate_data import main as validate_data  # noqa: E402


def load_dataset(path: Path) -> list[tuple[str, int]]:
    rows = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        text, label = raw_line.split("\t")
        rows.append((text, int(label)))
    return rows


def evaluate(path: Path) -> dict:
    rows = load_dataset(path)
    predictor = get_predictor()
    correct = 0
    details = []
    for text, label in rows:
        prediction = predictor.predict(text)
        correct += int(prediction.label_id == label)
        details.append(
            {
                "text": text,
                "label": label,
                "predicted_label": prediction.label_id,
                "confidence": prediction.confidence,
            }
        )
    accuracy = correct / len(rows) if rows else 0
    return {"file": str(path), "count": len(rows), "accuracy": round(accuracy, 4), "details": details}


def main() -> int:
    settings = get_settings()
    if validate_data() != 0:
        return 1

    reports_dir = PROJECT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    settings.model_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "note": "当前为训练骨架报告，真实 BERT 训练接入后替换为 accuracy、macro F1 和 classification_report。",
        "dev": evaluate(settings.data_dir / "dev.txt"),
        "test": evaluate(settings.data_dir / "test.txt"),
    }
    (reports_dir / "evaluation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 真实模型权重暂未生成，先写入占位元数据，保证训练流程有明确产物路径。
    placeholder = {
        "model_type": "bert-classifier-placeholder",
        "model_path": str(settings.model_path),
        "class_path": str(settings.class_path),
        "report_path": str(reports_dir / "evaluation_report.json"),
    }
    placeholder_path = settings.model_path.with_suffix(".placeholder.json")
    placeholder_path.write_text(json.dumps(placeholder, ensure_ascii=False, indent=2), encoding="utf-8")

    print("训练数据校验通过")
    print("BERT 训练骨架已就绪")
    print(f"预训练模型路径: {settings.bert_pretrained_path}")
    print(f"模型保存路径: {settings.model_path}")
    print(f"占位模型元数据: {placeholder_path}")
    print(f"评估报告: {reports_dir / 'evaluation_report.json'}")
    print("下一步接入 torch/transformers 训练循环，输出 accuracy、macro F1 和分类报告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
