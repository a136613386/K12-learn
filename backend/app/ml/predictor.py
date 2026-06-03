import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.ml.labels import KNOWLEDGE_POINTS


@dataclass
class PredictionResult:
    label_id: int
    confidence: float
    model_status: str


class BertKnowledgePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.tokenizer = None
        self.label_mapping: dict[int, str] = {}
        self.model_loaded = False
        self.model_status = "keyword_fallback"
        self.load_error: str | None = None
        self._load_model()

    def predict(self, text: str) -> PredictionResult:
        if self.model_loaded:
            return self._predict_with_model(text)
        return self._predict_with_keywords(text)

    def _load_model(self) -> None:
        model_dir = self.settings.model_path
        required = ["config.json", "label_mapping.json"]
        has_weight = any((model_dir / name).exists() for name in ["model.safetensors", "pytorch_model.bin"])
        has_tokenizer = any((model_dir / name).exists() for name in ["tokenizer.json", "vocab.txt"])
        missing = [name for name in required if not (model_dir / name).exists()]
        if not model_dir.is_dir() or missing or not has_weight or not has_tokenizer:
            if not model_dir.is_dir():
                self.load_error = f"model directory not found: {model_dir}"
            else:
                extra_missing = []
                if not has_weight:
                    extra_missing.append("model.safetensors or pytorch_model.bin")
                if not has_tokenizer:
                    extra_missing.append("tokenizer.json or vocab.txt")
                self.load_error = f"incomplete model directory: {', '.join(missing + extra_missing)}"
            return

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            label_mapping = json.loads((model_dir / "label_mapping.json").read_text(encoding="utf-8"))
            self.label_mapping = {int(key): value for key, value in label_mapping.items()}
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
            self.model.eval()
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model_loaded = True
            self.model_status = "bert"
            self.load_error = None
        except Exception as error:  # noqa: BLE001
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
            self.model_status = "keyword_fallback"
            self.load_error = str(error)

    def _predict_with_model(self, text: str) -> PredictionResult:
        import torch

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.no_grad():
            output = self.model(**encoded)
            probabilities = torch.softmax(output.logits, dim=-1).squeeze(0)
            confidence, label_tensor = torch.max(probabilities, dim=-1)

        return PredictionResult(
            label_id=int(label_tensor.item()),
            confidence=round(float(confidence.item()), 4),
            model_status="bert",
        )

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
            return PredictionResult(label_id=label_id, confidence=0.45, model_status="keyword_fallback")

        label_id = max(range(len(scores)), key=lambda idx: scores[idx])
        confidence = 1 / (1 + math.exp(-(scores[label_id] + 1)))
        return PredictionResult(
            label_id=label_id,
            confidence=round(min(confidence, 0.98), 4),
            model_status="keyword_fallback",
        )


_predictor: BertKnowledgePredictor | None = None


def get_predictor() -> BertKnowledgePredictor:
    global _predictor
    if _predictor is None:
        _predictor = BertKnowledgePredictor()
    return _predictor