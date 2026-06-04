import hashlib
import json
import math
from dataclasses import asdict, dataclass

from app.config import get_settings
from app.ml.fasttext_tokenizer import tokenize_text
from app.ml.labels import KNOWLEDGE_POINTS


@dataclass
class PredictionResult:
    label_id: int
    confidence: float
    model_status: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    bert_confidence: float | None = None
    fasttext_confidence: float | None = None

    def to_dict(self) -> dict:
        return {key: value for key, value in asdict(self).items() if value is not None}


class BertKnowledgePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.tokenizer = None
        self.fasttext_model = None
        self.label_mapping: dict[int, str] = {}
        self.fasttext_label_mapping: dict[int, str] = {}
        self.model_loaded = False
        self.bert_loaded = False
        self.fasttext_loaded = False
        self.model_status = "keyword_fallback"
        self.load_error: str | None = None
        self.bert_load_error: str | None = None
        self.fasttext_load_error: str | None = None
        self.device = None
        self._load_model()
        self._load_fasttext_model()
        self._refresh_aggregate_status()

    def predict(self, text: str) -> PredictionResult:
        bert_result = None
        if self.bert_loaded:
            bert_result = self._predict_with_model(text)
            bert_result.bert_confidence = bert_result.confidence
            if bert_result.confidence >= self.settings.bert_confidence_threshold:
                return bert_result

        fallback_reason = (
            "bert_confidence_below_threshold"
            if bert_result is not None
            else "bert_unavailable"
        )
        if self.fasttext_loaded:
            fasttext_result = self._predict_with_fasttext(text)
            fasttext_result.model_status = "fasttext_fallback"
            fasttext_result.fallback_used = True
            fasttext_result.fallback_reason = fallback_reason
            fasttext_result.fasttext_confidence = fasttext_result.confidence
            if bert_result is not None:
                fasttext_result.bert_confidence = bert_result.confidence
            return fasttext_result

        if bert_result is not None:
            bert_result.model_status = "bert_low_confidence_no_fasttext"
            bert_result.fallback_reason = "fasttext_unavailable"
            return bert_result

        return self._predict_with_keywords(text)

    def _load_model(self) -> None:
        model_dir = self.settings.model_path
        required = ["config.json", "label_mapping.json"]
        has_weight = any((model_dir / name).exists() for name in ["model.safetensors", "pytorch_model.bin"])
        has_tokenizer = any((model_dir / name).exists() for name in ["tokenizer.json", "vocab.txt"])
        missing = [name for name in required if not (model_dir / name).exists()]
        if not model_dir.is_dir() or missing or not has_weight or not has_tokenizer:
            if not model_dir.is_dir():
                self.bert_load_error = f"model directory not found: {model_dir}"
            else:
                extra_missing = []
                if not has_weight:
                    extra_missing.append("model.safetensors or pytorch_model.bin")
                if not has_tokenizer:
                    extra_missing.append("tokenizer.json or vocab.txt")
                self.bert_load_error = f"incomplete model directory: {', '.join(missing + extra_missing)}"
            self.load_error = self.bert_load_error
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
            self.bert_loaded = True
            self.bert_load_error = None
            self.load_error = None
        except Exception as error:  # noqa: BLE001
            self.model = None
            self.tokenizer = None
            self.bert_loaded = False
            self.bert_load_error = str(error)
            self.load_error = self.bert_load_error

    def _load_fasttext_model(self) -> None:
        model_dir = self.settings.fasttext_model_path
        model_path = model_dir / "model.bin"
        label_mapping_path = model_dir / "label_mapping.json"
        missing = [
            str(path.name)
            for path in [model_path, label_mapping_path]
            if not path.exists()
        ]
        if not model_dir.is_dir() or missing:
            if not model_dir.is_dir():
                self.fasttext_load_error = f"fasttext model directory not found: {model_dir}"
            else:
                self.fasttext_load_error = f"incomplete fasttext model directory: {', '.join(missing)}"
            return

        try:
            import fasttext  # type: ignore

            self.fasttext_model = fasttext.load_model(str(model_path))
            label_mapping = json.loads(label_mapping_path.read_text(encoding="utf-8"))
            self.fasttext_label_mapping = {int(key): value for key, value in label_mapping.items()}
            self.fasttext_loaded = True
            self.fasttext_load_error = None
        except Exception as error:  # noqa: BLE001
            self.fasttext_model = None
            self.fasttext_loaded = False
            self.fasttext_load_error = str(error)

    def _refresh_aggregate_status(self) -> None:
        self.model_loaded = self.bert_loaded or self.fasttext_loaded
        if self.bert_loaded:
            self.model_status = "bert"
        elif self.fasttext_loaded:
            self.model_status = "fasttext_fallback"
        else:
            self.model_status = "keyword_fallback"

        if self.bert_load_error and self.fasttext_load_error:
            self.load_error = f"BERT: {self.bert_load_error}; FastText: {self.fasttext_load_error}"
        else:
            self.load_error = self.bert_load_error or self.fasttext_load_error

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

    def _predict_with_fasttext(self, text: str) -> PredictionResult:
        tokenized = tokenize_text(text)
        labels, probabilities = self.fasttext_model.predict(tokenized, k=1)
        if not labels:
            raise RuntimeError("FastText predict returned no label")
        label_id = int(labels[0].replace("__label__", "", 1))
        confidence = float(probabilities[0]) if probabilities else 0.0
        return PredictionResult(
            label_id=label_id,
            confidence=round(confidence, 4),
            model_status="fasttext",
        )

    def _predict_with_keywords(self, text: str) -> PredictionResult:
        keyword_map = {
            0: ["\u5b5f\u5fb7\u5c14", "\u5206\u79bb\u6bd4", "\u663e\u6027", "\u9690\u6027", "\u8c4c\u8c46", "\u57fa\u56e0\u578b", "\u8868\u73b0\u578b"],
            1: ["\u51cf\u6570\u5206\u88c2", "\u53d7\u7cbe", "\u540c\u6e90\u67d3\u8272\u4f53", "\u67d3\u8272\u5355\u4f53", "DNA\u6570\u91cf"],
            2: ["\u4f34\u6027", "\u7ea2\u7eff\u8272\u76f2", "\u8272\u76f2", "X\u67d3\u8272\u4f53", "Y\u67d3\u8272\u4f53", "\u4f5d\u507b\u75c5"],
            3: ["\u80ba\u708e\u94fe\u7403\u83cc", "\u566c\u83cc\u4f53", "\u9057\u4f20\u7269\u8d28", "\u8f6c\u5316\u5b9e\u9a8c"],
            4: ["\u53cc\u87ba\u65cb", "\u78b1\u57fa\u4e92\u8865", "\u534a\u4fdd\u7559", "DNA\u590d\u5236", "\u590d\u5236"],
            5: ["\u8f6c\u5f55", "\u7ffb\u8bd1", "\u5bc6\u7801\u5b50", "\u6c28\u57fa\u9178", "\u86cb\u767d\u8d28\u5408\u6210"],
            6: ["\u57fa\u56e0\u8868\u8fbe", "\u6027\u72b6", "\u86cb\u767d\u8d28", "\u63a7\u5236\u6027\u72b6"],
            7: ["\u57fa\u56e0\u7a81\u53d8", "\u57fa\u56e0\u91cd\u7ec4", "\u7a81\u53d8", "\u91cd\u7ec4"],
            8: ["\u67d3\u8272\u4f53\u53d8\u5f02", "\u67d3\u8272\u4f53\u7ec4", "\u5355\u500d\u4f53", "\u591a\u500d\u4f53", "\u7ed3\u6784\u53d8\u5f02"],
            9: ["\u9057\u4f20\u75c5", "\u5355\u57fa\u56e0", "\u591a\u57fa\u56e0", "\u67d3\u8272\u4f53\u5f02\u5e38"],
            10: ["\u8428\u987f", "\u6469\u5c14\u6839", "\u679c\u8747", "\u57fa\u56e0\u5728\u67d3\u8272\u4f53\u4e0a"],
            11: ["\u81ea\u7136\u9009\u62e9", "\u57fa\u56e0\u9891\u7387", "\u7269\u79cd\u5f62\u6210", "\u8fdb\u5316"],
            12: ["\u5316\u77f3", "\u6bd4\u8f83\u89e3\u5256", "\u80da\u80ce\u5b66", "\u5171\u540c\u7956\u5148"],
            13: ["\u534f\u540c\u8fdb\u5316", "\u5171\u540c\u8fdb\u5316", "\u751f\u7269\u591a\u6837\u6027"],
            14: ["\u6a21\u62df\u5b9e\u9a8c", "\u6a21\u578b\u5b9e\u9a8c", "\u8c03\u67e5\u5b9e\u9a8c", "\u89c2\u5bdf\u5b9e\u9a8c", "\u63a2\u7a76"],
        }

        scores = []
        for item in KNOWLEDGE_POINTS:
            score = sum(1 for keyword in keyword_map[item["id"]] if keyword in text)
            scores.append(score)

        if max(scores) == 0:
            digest = hashlib.md5(text.encode("utf-8")).hexdigest()
            label_id = int(digest[:4], 16) % len(KNOWLEDGE_POINTS)
            return PredictionResult(
                label_id=label_id,
                confidence=0.45,
                model_status="keyword_fallback",
                fallback_used=True,
                fallback_reason="bert_and_fasttext_unavailable",
            )

        label_id = max(range(len(scores)), key=lambda idx: scores[idx])
        confidence = 1 / (1 + math.exp(-(scores[label_id] + 1)))
        return PredictionResult(
            label_id=label_id,
            confidence=round(min(confidence, 0.98), 4),
            model_status="keyword_fallback",
            fallback_used=True,
            fallback_reason="bert_and_fasttext_unavailable",
        )


_predictor: BertKnowledgePredictor | None = None


def get_predictor() -> BertKnowledgePredictor:
    global _predictor
    if _predictor is None:
        _predictor = BertKnowledgePredictor()
    return _predictor
