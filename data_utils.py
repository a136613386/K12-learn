import json
import os

import jieba
import pandas as pd
from sklearn.model_selection import train_test_split

from config import Config


def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def _build_label_map(df: pd.DataFrame) -> dict:
    required_columns = {"knowledge_points", "knowledge_points_id"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV 缺少必要列: {', '.join(sorted(missing))}")

    unique_pairs = (
        df[["knowledge_points_id", "knowledge_points"]]
        .dropna()
        .drop_duplicates()
        .sort_values(by="knowledge_points_id")
    )

    id_to_name = {}
    name_to_id = {}
    for _, row in unique_pairs.iterrows():
        knowledge_id = int(row["knowledge_points_id"])
        knowledge_name = _normalize_text(row["knowledge_points"])
        if not knowledge_name:
            continue
        id_to_name[str(knowledge_id)] = knowledge_name
        name_to_id[knowledge_name] = knowledge_id

    if not id_to_name:
        raise ValueError("未从 CSV 中解析到任何有效的知识点映射")

    return {"id_to_name": id_to_name, "name_to_id": name_to_id}


def _build_fasttext_line(row: pd.Series) -> str:
    knowledge_id = int(row["knowledge_points_id"])
    question = _normalize_text(row.get("question", ""))
    option_text = _normalize_text(row.get("option", ""))

    text_parts = [part for part in [question, option_text] if part]
    if not text_parts:
        raise ValueError(f"知识点 {knowledge_id} 存在空题目记录")

    segmented_text = " ".join(jieba.lcut(" ".join(text_parts)))
    return f"__label__{knowledge_id} {segmented_text}"


def preprocess_and_split() -> dict:
    print("=== [开始预处理 CSV 数据] ===")

    if not os.path.exists(Config.RAW_DATA_PATH):
        raise FileNotFoundError(f"未找到原始数据文件: {Config.RAW_DATA_PATH}")

    df = pd.read_csv(Config.RAW_DATA_PATH, encoding="utf-8-sig")
    if df.empty:
        raise ValueError("原始数据为空，无法训练模型")

    label_map = _build_label_map(df)
    fasttext_lines = [_build_fasttext_line(row) for _, row in df.iterrows()]

    train_lines, val_lines = train_test_split(
        fasttext_lines,
        test_size=Config.TEST_SIZE,
        random_state=Config.RANDOM_SEED,
        shuffle=True,
    )

    with open(Config.TRAIN_TXT, "w", encoding="utf-8") as train_file:
        train_file.write("\n".join(train_lines) + "\n")

    with open(Config.VAL_TXT, "w", encoding="utf-8") as val_file:
        val_file.write("\n".join(val_lines) + "\n")

    with open(Config.LABEL_MAP_PATH, "w", encoding="utf-8") as label_file:
        json.dump(label_map, label_file, ensure_ascii=False, indent=2)

    print(f"训练集已生成: {Config.TRAIN_TXT} ({len(train_lines)} 条)")
    print(f"验证集已生成: {Config.VAL_TXT} ({len(val_lines)} 条)")
    print(f"标签映射已更新: {Config.LABEL_MAP_PATH}")

    return {
        "train_count": len(train_lines),
        "val_count": len(val_lines),
        "label_count": len(label_map["id_to_name"]),
    }


if __name__ == "__main__":
    preprocess_and_split()
