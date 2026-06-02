import hashlib
import math
from dataclasses import dataclass

from app.config import get_settings
from app.ml.labels import KNOWLEDGE_POINTS


@dataclass
class PredictionResult:
    label_id: int
    confidence: float


class BertKnowledgePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_loaded = self.settings.model_path.exists()

    def predict(self, text: str) -> PredictionResult:
        if self.model_loaded:
            return self._predict_with_model(text)
        return self._predict_with_keywords(text)

    def _predict_with_model(self, text: str) -> PredictionResult:
        # 这里预留真实 BERT 推理入口，后续加载 tokenizer、模型权重并返回 softmax 结果。
        return self._predict_with_keywords(text)

    def _predict_with_keywords(self, text: str) -> PredictionResult:
        keyword_map = {
            0: ["孟德尔", "分离比", "显性", "隐性", "豌豆", "基因型", "表现型"],
            1: ["减数分裂", "受精", "同源染色体", "染色单体", "DNA数量"],
            2: ["伴性", "红绿色盲", "色盲", "X染色体", "Y染色体", "佝偻病"],
            3: ["肺炎链球菌", "噬菌体", "遗传物质", "转化实验"],
            4: ["双螺旋", "碱基互补", "半保留", "DNA复制", "复制"],
            5: ["转录", "翻译", "密码子", "氨基酸", "蛋白质合成"],
            6: ["基因表达", "性状", "蛋白质", "控制性状"],
            7: ["基因突变", "基因重组", "突变", "重组"],
            8: ["染色体变异", "染色体组", "单倍体", "多倍体", "结构变异"],
            9: ["遗传病", "单基因", "多基因", "染色体异常"],
            10: ["萨顿", "摩尔根", "果蝇", "基因在染色体上"],
            11: ["自然选择", "基因频率", "物种形成", "进化"],
            12: ["化石", "比较解剖", "胚胎学", "共同祖先"],
            13: ["协同进化", "共同进化", "生物多样性"],
            14: ["模拟实验", "模型实验", "调查实验", "观察实验", "探究"],
        }

        scores = []
        for item in KNOWLEDGE_POINTS:
            score = sum(1 for keyword in keyword_map[item["id"]] if keyword in text)
            scores.append(score)

        if max(scores) == 0:
            digest = hashlib.md5(text.encode("utf-8")).hexdigest()
            label_id = int(digest[:4], 16) % len(KNOWLEDGE_POINTS)
            return PredictionResult(label_id=label_id, confidence=0.45)

        label_id = max(range(len(scores)), key=lambda idx: scores[idx])
        confidence = 1 / (1 + math.exp(-(scores[label_id] + 1)))
        return PredictionResult(label_id=label_id, confidence=round(min(confidence, 0.98), 4))


_predictor: BertKnowledgePredictor | None = None


def get_predictor() -> BertKnowledgePredictor:
    global _predictor
    if _predictor is None:
        _predictor = BertKnowledgePredictor()
    return _predictor
