# predict.py
import jieba
import fasttext
import os
import json
from config import Config


class BioPredictor:
    def __init__(self):
        if not os.path.exists(Config.MODEL_PATH):
            raise FileNotFoundError(f"找不到训练好的模型文件，请先运行 train.py。路径: {Config.MODEL_PATH}")
        if not os.path.exists(Config.LABEL_MAP_PATH):
            raise FileNotFoundError(f"找不到分类映射文件，路径: {Config.LABEL_MAP_PATH}")

        # 加载 FastText 模型
        self.model = fasttext.load_model(Config.MODEL_PATH)

        # 加载分类ID映射文件
        with open(Config.LABEL_MAP_PATH, 'r', encoding='utf-8') as f:
            self.label_data = json.load(f)
            self.name_to_id = self.label_data["name_to_id"]

    def predict(self, question_text, threshold=None):
        if threshold is None:
            threshold = Config.DEFAULT_THRESHOLD

        # 1. 对输入题目清洗换行并进行中文分词
        clean_text = question_text.replace('\n', ' ').replace('\r', '')
        segmented_text = " ".join(jieba.lcut(clean_text))

        # 2. 预测所有满足阈值的标签
        labels, probabilities = self.model.predict(segmented_text, k=-1, threshold=threshold)

        # 3. 结合 label_map 格式化输出
        results = []
        for label, prob in zip(labels, probabilities):
            clean_name = label.replace("__label__", "")
            # 自动获取对应的标准 ID，如果找不到则返回 -1
            knowledge_id = self.name_to_id.get(clean_name, -1)

            results.append({
                "knowledge_id": knowledge_id,
                "knowledge_point": clean_name,
                "confidence": round(float(prob), 4)
            })

        return results


# 测试推理效果
if __name__ == "__main__":
    try:
        predictor = BioPredictor()

        # 拿两道新题测试一下效果
        test_q = (
            "题干：下列哪项最能说明豌豆适合作为孟德尔遗传实验材料？选项：A、豌豆花大而鲜艳，主要用于观赏B、豌豆自然状态下一般为纯种，且有易区分的相对性状C、豌豆没有种子，便于统计D、豌豆只能进行异花传粉")
        res = predictor.predict(test_q)

        print(f"\n【测试题目】: {test_q}")
        print("【预测结果（含分类ID）】:")
        for r in res:
            print(
                f"  - ID: {r['knowledge_id']} | 知识点: {r['knowledge_point']} (置信度: {r['confidence'] * 100:.2f}%)")

    except Exception as e:
        print(f"发生错误: {e}")
