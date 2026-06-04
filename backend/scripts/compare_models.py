import json
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_DIR / "reports"
BERT_REPORT_PATH = REPORTS_DIR / "evaluation_report.json"
FASTTEXT_REPORT_PATH = REPORTS_DIR / "fasttext_evaluation_report.json"
COMPARISON_REPORT_PATH = REPORTS_DIR / "model_comparison_report.json"


class ModelComparisonError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_placeholder_report(report: dict[str, Any] | None) -> bool:
    if not report:
        return True
    note = str(report.get("note", ""))
    if "占位" in note or "骨架" in note or "placeholder" in note.lower():
        return True
    return "test_accuracy" not in report or "test_macro_f1" not in report


def file_size(path_value: str | None) -> int | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_dir():
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    if path.exists():
        return path.stat().st_size
    return None


def summarize_bert(report: dict[str, Any] | None) -> dict[str, Any]:
    if is_placeholder_report(report):
        return {
            "available": False,
            "reason": "BERT 评估报告缺失、被删除或仍是占位报告",
            "report_path": str(BERT_REPORT_PATH),
        }
    model_dir = report.get("model_dir")
    return {
        "available": True,
        "report_path": str(BERT_REPORT_PATH),
        "test_accuracy": report.get("test_accuracy"),
        "test_macro_f1": report.get("test_macro_f1"),
        "train_elapsed_seconds": report.get("train_elapsed_seconds"),
        "avg_inference_ms": report.get("avg_inference_ms"),
        "model_path": model_dir,
        "model_size_bytes": file_size(model_dir),
        "training_args": report.get("training_args", {}),
        "train_count": report.get("train_count"),
        "dev_count": report.get("dev_count"),
        "test_count": report.get("test_count"),
    }


def summarize_fasttext(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        raise ModelComparisonError(f"FastText 评估报告不存在，请先运行训练脚本: {FASTTEXT_REPORT_PATH}")
    required = ["test_accuracy", "test_macro_f1", "model_path"]
    missing = [field for field in required if field not in report]
    if missing:
        raise ModelComparisonError(f"FastText 评估报告缺少字段: {', '.join(missing)}")
    return {
        "available": True,
        "report_path": str(FASTTEXT_REPORT_PATH),
        "test_accuracy": report.get("test_accuracy"),
        "test_macro_f1": report.get("test_macro_f1"),
        "train_elapsed_seconds": report.get("train_elapsed_seconds"),
        "avg_inference_ms": report.get("avg_inference_ms"),
        "model_path": report.get("model_path"),
        "model_size_bytes": report.get("model_size_bytes") or file_size(report.get("model_path")),
        "training_args": report.get("training_args", {}),
        "train_count": report.get("train_count"),
        "dev_count": report.get("dev_count"),
        "test_count": report.get("test_count"),
    }


def choose_recommendation(bert: dict[str, Any], fasttext: dict[str, Any]) -> str:
    if not bert.get("available"):
        return "FastText: BERT 指标不可用，当前只能基于 FastText 实测结果决策。"
    bert_f1 = float(bert.get("test_macro_f1") or 0)
    fasttext_f1 = float(fasttext.get("test_macro_f1") or 0)
    bert_latency = bert.get("avg_inference_ms")
    fasttext_latency = fasttext.get("avg_inference_ms")
    if fasttext_f1 >= bert_f1 - 0.03:
        return "FastText: macro F1 接近或优于 BERT，且推理和部署成本更低。"
    if fasttext_latency is not None and bert_latency is not None and float(fasttext_latency) < float(bert_latency):
        return "需要权衡: BERT 指标更高，但 FastText 延迟更低。"
    return "BERT: 当前指标优势明显。"


def main() -> int:
    try:
        bert_report = read_json(BERT_REPORT_PATH)
        fasttext_report = read_json(FASTTEXT_REPORT_PATH)
        bert = summarize_bert(bert_report)
        fasttext = summarize_fasttext(fasttext_report)
        comparison = {
            "bert": bert,
            "fasttext": fasttext,
            "recommendation": choose_recommendation(bert, fasttext),
            "notes": [
                "BERT 报告缺失或占位时，不参与指标比较。",
                "FastText 指标来自 reports/fasttext_evaluation_report.json。",
            ],
        }
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        COMPARISON_REPORT_PATH.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"模型对比报告已生成: {COMPARISON_REPORT_PATH}")
        print(comparison["recommendation"])
        return 0
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
