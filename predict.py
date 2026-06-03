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
            "学家发现染色体主要是由蛋白质和DNA组成。关于证明蛋白质和核酸哪一种是遗传物质的系列实验，下列叙述正确的是"
            "- - A．肺炎链球菌体内转化实验中，加热致死的S型菌株的DNA分子在小鼠体内可使R型活菌的相对性状从无致病性转化为有致病性"
            "- B．肺炎链球菌体外转化实验中，利用自变量控制的“加法原理”，将“S型菌DNA+DNA酶”加入R型活菌的培养基中，结果证明DNA是转化因子"
            "- C．噬菌体侵染实验中，用放射性同位素分别标记了噬菌体的蛋白质外壳和DNA，发现其DNA进入宿主细胞后，利用自身原料和酶完成自我复制"
            "- D．烟草花叶病毒实验中，以病毒颗粒的RNA和蛋白质互为对照进行侵染，结果发现自变量RNA分子可使烟草出现花叶病斑性状"
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
