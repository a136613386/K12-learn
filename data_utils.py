# data_utils.py
import json
import os
import jieba
from sklearn.model_selection import train_test_split
from config import Config


def preprocess_and_split():
    print("=== [开始数据预处理] ===")

    if not os.path.exists(Config.RAW_JSON_DATA):
        raise FileNotFoundError(f"未找到原始数据文件: {Config.RAW_JSON_DATA}")

    with open(Config.RAW_JSON_DATA, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    fasttext_lines = []

    for item in raw_data:
        # 1. 标签处理：加前缀并去除内部空格
        label_string = " ".join([f"__label__{label.replace(' ', '')}" for label in item['labels']])

        # 2. 文本处理：jieba分词，清洗换行
        clean_question = item['question'].replace('\n', ' ').replace('\r', '')
        words_string = " ".join(jieba.lcut(clean_question))

        # 3. 拼接单行
        full_line = f"{label_string} {words_string}"
        fasttext_lines.append(full_line)

    # 划分数据集
    train_lines, val_lines = train_test_split(
        fasttext_lines,
        test_size=Config.TEST_SIZE,
        random_state=Config.RANDOM_SEED
    )

    # 保存为 FastText 识别的 txt
    with open(Config.TRAIN_TXT, 'w', encoding='utf-8') as f:
        f.write("\n".join(train_lines) + "\n")

    with open(Config.VAL_TXT, 'w', encoding='utf-8') as f:
        f.write("\n".join(val_lines) + "\n")

    print(f"数据处理完成！训练集: {len(train_lines)}条，验证集: {len(val_lines)}条。")


if __name__ == "__main__":
    preprocess_and_split()