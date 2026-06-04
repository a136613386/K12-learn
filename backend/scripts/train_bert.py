import argparse
import json
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / "backend"))

from app.config import get_settings  # noqa: E402
from scripts.validate_data import main as validate_data  # noqa: E402


DEFAULT_BASE_MODEL_NAME = "bert-base-chinese"


def load_dataset(path: Path) -> list[tuple[str, int]]:
    rows = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        text, label = raw_line.split("\t")
        rows.append((text, int(label)))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train BERT knowledge-point classifier")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--base-model-name", default=DEFAULT_BASE_MODEL_NAME)
    parser.add_argument("--dry-run", action="store_true", help="Validate data and config without training")
    return parser.parse_args()


def is_reference_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return "04-bert" in normalized or "work_heima" in normalized


def is_complete_model_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    has_config = (path / "config.json").exists()
    has_tokenizer = any((path / name).exists() for name in ["tokenizer.json", "vocab.txt"])
    has_weight = any((path / name).exists() for name in ["model.safetensors", "pytorch_model.bin"])
    return has_config and has_tokenizer and has_weight


def check_training_environment(settings) -> None:
    if is_reference_path(settings.bert_pretrained_path):
        raise ValueError(
            "BERT_PRETRAINED_PATH must not point to the reference project 04-bert directory. "
            f"Current path: {settings.bert_pretrained_path}"
        )
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as error:
        raise RuntimeError("Missing training dependencies: torch, transformers or scikit-learn") from error


def resolve_pretrained_source(settings, base_model_name: str) -> tuple[str | Path, bool]:
    if is_complete_model_dir(settings.bert_pretrained_path):
        return settings.bert_pretrained_path, False
    return base_model_name, True


def load_labels(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    args = parse_args()
    settings = get_settings()
    if validate_data() != 0:
        return 1

    check_training_environment(settings)
    train_rows = load_dataset(settings.data_dir / "train.txt")
    dev_rows = load_dataset(settings.data_dir / "dev.txt")
    test_rows = load_dataset(settings.data_dir / "test.txt")
    labels = load_labels(settings.class_path)
    pretrained_source, will_prepare_base_model = resolve_pretrained_source(settings, args.base_model_name)

    if args.dry_run:
        print("BERT training dry-run passed")
        print(f"train={len(train_rows)}, dev={len(dev_rows)}, test={len(test_rows)}, labels={len(labels)}")
        print(f"bert_pretrained_path={settings.bert_pretrained_path}")
        print(f"base_model_source={pretrained_source}")
        print(f"will_prepare_base_model={will_prepare_base_model}")
        print(f"model_path={settings.model_path}")
        return 0

    import torch
    from sklearn.metrics import accuracy_score, classification_report, f1_score
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    class TextDataset(Dataset):
        def __init__(self, rows, tokenizer):
            self.rows = rows
            self.tokenizer = tokenizer

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, index):
            text, label = self.rows[index]
            encoded = self.tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=args.max_length,
                return_tensors="pt",
            )
            return {
                "input_ids": encoded["input_ids"].squeeze(0),
                "attention_mask": encoded["attention_mask"].squeeze(0),
                "labels": torch.tensor(label, dtype=torch.long),
            }

    def evaluate(model, loader, device):
        model.eval()
        preds, golds = [], []
        with torch.no_grad():
            for batch in loader:
                batch = {key: value.to(device) for key, value in batch.items()}
                output = model(**batch)
                preds.extend(output.logits.argmax(dim=-1).cpu().tolist())
                golds.extend(batch["labels"].cpu().tolist())
        return {
            "accuracy": accuracy_score(golds, preds),
            "macro_f1": f1_score(golds, preds, average="macro"),
            "classification_report": classification_report(golds, preds, target_names=labels, zero_division=0),
        }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(pretrained_source)
    model = AutoModelForSequenceClassification.from_pretrained(
        pretrained_source, num_labels=len(labels)
    ).to(device)

    if will_prepare_base_model:
        settings.bert_pretrained_path.mkdir(parents=True, exist_ok=True)
        tokenizer.save_pretrained(settings.bert_pretrained_path)
        model.save_pretrained(settings.bert_pretrained_path)

    train_loader = DataLoader(TextDataset(train_rows, tokenizer), batch_size=args.batch_size, shuffle=True)
    dev_loader = DataLoader(TextDataset(dev_rows, tokenizer), batch_size=args.batch_size)
    test_loader = DataLoader(TextDataset(test_rows, tokenizer), batch_size=args.batch_size)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    total_steps = max(1, len(train_loader) * args.epochs)
    scheduler = get_linear_schedule_with_warmup(optimizer, 0, total_steps)
    best_macro_f1 = -1.0
    output_dir = settings.model_path
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            output = model(**batch)
            output.loss.backward()
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        dev_metrics = evaluate(model, dev_loader, device)
        print(f"epoch={epoch + 1}, dev_accuracy={dev_metrics['accuracy']:.4f}, dev_macro_f1={dev_metrics['macro_f1']:.4f}")
        if dev_metrics["macro_f1"] > best_macro_f1:
            best_macro_f1 = dev_metrics["macro_f1"]
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)

    model = AutoModelForSequenceClassification.from_pretrained(output_dir).to(device)
    test_metrics = evaluate(model, test_loader, device)
    reports_dir = PROJECT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    label_mapping_path = output_dir / "label_mapping.json"
    label_mapping_path.write_text(
        json.dumps({str(i): label for i, label in enumerate(labels)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "training_args": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "learning_rate": args.learning_rate,
            "base_model_name": args.base_model_name,
        },
        "train_count": len(train_rows),
        "dev_count": len(dev_rows),
        "test_count": len(test_rows),
        "label_count": len(labels),
        "best_dev_macro_f1": best_macro_f1,
        "test_accuracy": test_metrics["accuracy"],
        "test_macro_f1": test_metrics["macro_f1"],
        "classification_report": test_metrics["classification_report"],
        "model_dir": str(output_dir),
        "bert_pretrained_path": str(settings.bert_pretrained_path),
        "base_model_source": str(pretrained_source),
        "base_model_cache_created": will_prepare_base_model,
        "label_mapping_path": str(label_mapping_path),
    }
    (reports_dir / "evaluation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"model_dir={output_dir}")
    print(f"evaluation_report={reports_dir / 'evaluation_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())