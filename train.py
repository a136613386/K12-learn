# train.py
import fasttext
import os
from config import Config
from data_utils import preprocess_and_split


def main():
    # 1. 确保训练数据存在（如果不存在则先跑数据处理）
    preprocess_and_split()

    print("\n=== [开始训练 FastText 模型] ===")
    # 2. 传入 config 中的超参数进行训练
    model = fasttext.train_supervised(
        input=Config.TRAIN_TXT,
        lr=Config.LR,
        epoch=Config.EPOCH,
        wordNgrams=Config.WORD_NGRAMS,
        loss=Config.LOSS_FUNC,
        dim=Config.DIM
    )

    # 3. 保存模型
    model.save_model(Config.MODEL_PATH)
    print(f"模型训练成功，已保存至: {Config.MODEL_PATH}")

    # 4. 评估模型
    print("\n=== [模型评估指标] ===")
    samples_num, precision, recall = model.test(Config.VAL_TXT, k=-1, threshold=0.5)

    print(f"评估样本总数: {samples_num}")
    print(f"准确率 (Precision): {precision:.4f}")
    print(f"召回率 (Recall): {recall:.4f}")

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
        print(f"综合 F1-Score: {f1:.4f}")


if __name__ == "__main__":
    main()