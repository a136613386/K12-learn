import fasttext

from config import Config
from data_utils import preprocess_and_split


def calculate_f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def print_metrics(model, dataset_path: str, dataset_name: str) -> None:
    sample_count, precision, recall = model.test(
        dataset_path,
        k=1,
    )
    f1 = calculate_f1(precision, recall)

    print(f"[{dataset_name}] 样本数: {sample_count}")
    print(f"[{dataset_name}] Precision: {precision:.4f}")
    print(f"[{dataset_name}] Recall: {recall:.4f}")
    print(f"[{dataset_name}] F1: {f1:.4f}")


def main():
    summary = preprocess_and_split()
    print(
        f"共准备 {summary['label_count']} 个知识点，"
        f"{summary['train_count']} 条训练数据，"
        f"{summary['val_count']} 条验证数据。"
    )

    print("\n=== [开始训练 FastText 模型] ===")
    model = fasttext.train_supervised(
        input=Config.TRAIN_TXT,
        lr=Config.LR,
        epoch=Config.EPOCH,
        wordNgrams=Config.WORD_NGRAMS,
        loss=Config.LOSS_FUNC,
        dim=Config.DIM,
    )

    model.save_model(Config.MODEL_PATH)
    print(f"模型已保存到: {Config.MODEL_PATH}")

    print("\n=== [模型评估] ===")
    print_metrics(model, Config.TRAIN_TXT, "训练集")
    print_metrics(model, Config.VAL_TXT, "验证集")


if __name__ == "__main__":
    main()
