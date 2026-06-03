import json
import os
import sys

import fasttext
import jieba

from config import Config


class BioPredictor:
    def __init__(self):
        if not os.path.exists(Config.MODEL_PATH):
            raise FileNotFoundError(
                f"找不到训练好的模型文件，请先运行 train.py。路径: {Config.MODEL_PATH}"
            )
        if not os.path.exists(Config.LABEL_MAP_PATH):
            raise FileNotFoundError(
                f"找不到标签映射文件，请先运行 train.py。路径: {Config.LABEL_MAP_PATH}"
            )

        self.model = fasttext.load_model(Config.MODEL_PATH)
        with open(Config.LABEL_MAP_PATH, "r", encoding="utf-8") as label_file:
            label_data = json.load(label_file)

        self.id_to_name = label_data.get("id_to_name", {})
        self.name_to_id = label_data.get("name_to_id", {})

    def predict(self, question_text: str, threshold=None):
        threshold = Config.DEFAULT_THRESHOLD if threshold is None else threshold

        clean_text = question_text.replace("\n", " ").replace("\r", " ").strip()
        if not clean_text:
            return []

        segmented_text = " ".join(jieba.lcut(clean_text))
        labels, probabilities = self.model.predict(
            segmented_text,
            k=-1,
            threshold=threshold,
        )

        results = []
        for label, prob in zip(labels, probabilities):
            raw_label = label.replace("__label__", "")
            knowledge_id = self.name_to_id.get(raw_label)
            knowledge_name = raw_label

            if raw_label.isdigit():
                knowledge_id = int(raw_label)
                knowledge_name = self.id_to_name.get(raw_label, raw_label)
            elif knowledge_id is None:
                knowledge_id = -1

            results.append(
                {
                    "knowledge_id": knowledge_id,
                    "knowledge_point": knowledge_name,
                    "confidence": round(float(prob), 4),
                }
            )

        return results


def main():
    predictor = BioPredictor()
    sample_text = " ".join(sys.argv[1:]).strip()
    if not sample_text:
        sample_text = (
            "假说—演绎法是科学研究中常用的方法，包括“提出问题、作出假说、演绎推理、实验验证、得出结论”五个基本环节，利用该方法，孟德尔发现了两大遗传定律.下列关于孟德尔研究过程的分析，错误的是(　　)"
            "A、豌豆花大而鲜艳，主要用于观赏 "
            "B、豌豆自然状态下一般为纯种，且有易区分的相对性状 "
            "C、豌豆没有种子，便于统计 "
            "D、豌豆只能进行异花传粉"
        )

    results = predictor.predict(sample_text)
    print(f"输入题目: {sample_text}")
    if not results:
        print("没有命中任何标签，请尝试降低阈值或检查模型。")
        return

    print("预测结果:")
    for item in results:
        print(
            f"- ID: {item['knowledge_id']} | "
            f"知识点: {item['knowledge_point']} | "
            f"置信度: {item['confidence']:.4f}"
        )


if __name__ == "__main__":
    main()
