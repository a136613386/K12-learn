import argparse
import json
from pathlib import Path
import sys
import time

from sklearn.metrics import accuracy_score, classification_report, f1_score


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from scripts.preprocess_fasttext_dataset import (  # noqa: E402
    FASTTEXT_DIR,
    REPORT_PATH as PREPROCESS_REPORT_PATH,
    TOKENIZATION_MODE,
    load_labels,
    main as preprocess_fasttext_dataset,
)


MODEL_DIR = PROJECT_DIR / "backend" / "models" / "fasttext_knowledge"
MODEL_PATH = MODEL_DIR / "model.bin"
LABEL_MAPPING_PATH = MODEL_DIR / "label_mapping.json"
TOKENIZATION_CONFIG_PATH = MODEL_DIR / "tokenization_config.json"
REPORTS_DIR = PROJECT_DIR / "reports"
EVALUATION_REPORT_PATH = REPORTS_DIR / "fasttext_evaluation_report.json"


class FastTextTrainingError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train FastText knowledge-point classifier")
    parser.add_argument("--epoch", type=int, default=25)
    parser.add_argument("--lr", type=float, default=0.5)
    parser.add_argument("--word-ngrams", type=int, default=2)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--dim", type=int, default=100)
    parser.add_argument("--bucket", type=int, default=100000)
    parser.add_argument("--loss", default="softmax", choices=["softmax", "ova", "hs", "ns"])
    parser.add_argument("--preprocess", action="store_true", help="Regenerate FastText split files before training")
    return parser.parse_args()


def import_fasttext():
    try:
        import fasttext  # type: ignore
    except ImportError as error:
        raise FastTextTrainingError(
            "缺少 FastText 依赖。请先运行: python -m pip install fasttext-wheel>=0.9.2"
        ) from error
    return fasttext


def load_fasttext_rows(path: Path) -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    if not path.exists():
        raise FastTextTrainingError(f"FastText 数据文件不存在: {path}")
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        label, _, text = line.partition(" ")
        if not label.startswith("__label__") or not text:
            raise FastTextTrainingError(f"{path.name}:{line_no} 不是有效 FastText 监督格式")
        try:
            label_id = int(label.replace("__label__", "", 1))
        except ValueError as error:
            raise FastTextTrainingError(f"{path.name}:{line_no} 标签不是整数: {label}") from error
        rows.append((text, label_id))
    return rows


def predict_label(model, text: str) -> int:
    labels, _ = model.predict(text, k=1)
    if not labels:
        raise FastTextTrainingError("FastText predict 未返回标签")
    return int(labels[0].replace("__label__", "", 1))


def evaluate_model(model, rows: list[tuple[str, int]], labels: list[str]) -> dict:
    golds = [label_id for _, label_id in rows]
    preds = [predict_label(model, text) for text, _ in rows]
    return {
        "accuracy": accuracy_score(golds, preds),
        "macro_f1": f1_score(golds, preds, average="macro", labels=list(range(len(labels))), zero_division=0),
        "classification_report": classification_report(
            golds,
            preds,
            labels=list(range(len(labels))),
            target_names=labels,
            zero_division=0,
        ),
        "prediction_distribution": {
            str(label_id): preds.count(label_id)
            for label_id in sorted(set(preds))
        },
    }


def average_inference_ms(model, rows: list[tuple[str, int]]) -> float:
    if not rows:
        return 0.0
    sample_rows = rows[: min(200, len(rows))]
    start = time.perf_counter()
    for text, _ in sample_rows:
        model.predict(text, k=1)
    elapsed = time.perf_counter() - start
    return round(elapsed * 1000 / len(sample_rows), 4)


def ensure_fasttext_data() -> None:
    required = [FASTTEXT_DIR / f"{split}.txt" for split in ["train", "dev", "test"]]
    if all(path.exists() for path in required):
        return
    exit_code = preprocess_fasttext_dataset()
    if exit_code != 0:
        raise FastTextTrainingError("FastText 数据预处理失败")


def main() -> int:
    args = parse_args()
    try:
        fasttext = import_fasttext()
        labels = load_labels()
        if args.preprocess:
            exit_code = preprocess_fasttext_dataset()
            if exit_code != 0:
                return exit_code
        else:
            ensure_fasttext_data()

        train_path = FASTTEXT_DIR / "train.txt"
        dev_path = FASTTEXT_DIR / "dev.txt"
        test_path = FASTTEXT_DIR / "test.txt"
        train_rows = load_fasttext_rows(train_path)
        dev_rows = load_fasttext_rows(dev_path)
        test_rows = load_fasttext_rows(test_path)

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        train_start = time.perf_counter()
        model = fasttext.train_supervised(
            input=str(train_path),
            epoch=args.epoch,
            lr=args.lr,
            wordNgrams=args.word_ngrams,
            minCount=args.min_count,
            dim=args.dim,
            bucket=args.bucket,
            loss=args.loss,
            verbose=2,
        )
        train_elapsed_seconds = round(time.perf_counter() - train_start, 4)

        dev_metrics = evaluate_model(model, dev_rows, labels)
        test_metrics = evaluate_model(model, test_rows, labels)
        avg_inference_ms = average_inference_ms(model, test_rows)

        model.save_model(str(MODEL_PATH))
        LABEL_MAPPING_PATH.write_text(
            json.dumps({str(index): label for index, label in enumerate(labels)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tokenization_config = {
            "mode": TOKENIZATION_MODE,
            "description": "中文按字符切分，连续英文/数字/遗传符号保留为 token",
            "preprocess_report": str(PREPROCESS_REPORT_PATH),
        }
        TOKENIZATION_CONFIG_PATH.write_text(json.dumps(tokenization_config, ensure_ascii=False, indent=2), encoding="utf-8")

        report = {
            "training_args": {
                "epoch": args.epoch,
                "lr": args.lr,
                "wordNgrams": args.word_ngrams,
                "minCount": args.min_count,
                "dim": args.dim,
                "bucket": args.bucket,
                "loss": args.loss,
            },
            "train_count": len(train_rows),
            "dev_count": len(dev_rows),
            "test_count": len(test_rows),
            "label_count": len(labels),
            "dev_accuracy": dev_metrics["accuracy"],
            "dev_macro_f1": dev_metrics["macro_f1"],
            "test_accuracy": test_metrics["accuracy"],
            "test_macro_f1": test_metrics["macro_f1"],
            "classification_report": test_metrics["classification_report"],
            "dev_prediction_distribution": dev_metrics["prediction_distribution"],
            "test_prediction_distribution": test_metrics["prediction_distribution"],
            "model_path": str(MODEL_PATH),
            "model_size_bytes": MODEL_PATH.stat().st_size,
            "label_mapping_path": str(LABEL_MAPPING_PATH),
            "tokenization": tokenization_config,
            "data_paths": {
                "train": str(train_path),
                "dev": str(dev_path),
                "test": str(test_path),
            },
            "train_elapsed_seconds": train_elapsed_seconds,
            "avg_inference_ms": avg_inference_ms,
        }
        EVALUATION_REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(
            "FastText 训练完成: "
            f"dev_accuracy={dev_metrics['accuracy']:.4f}, dev_macro_f1={dev_metrics['macro_f1']:.4f}, "
            f"test_accuracy={test_metrics['accuracy']:.4f}, test_macro_f1={test_metrics['macro_f1']:.4f}"
        )
        print(f"model_path={MODEL_PATH}")
        print(f"evaluation_report={EVALUATION_REPORT_PATH}")
        return 0
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
