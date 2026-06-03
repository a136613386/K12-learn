from __future__ import annotations

from app.ml.labels import KNOWLEDGE_POINTS


QUESTION_TEMPLATES = [
    "\u5173\u4e8e\u201c{label}\u201d\uff0c\u4e0b\u5217\u8bf4\u6cd5\u6b63\u786e\u7684\u662f\u54ea\u4e00\u9879\uff1f",
    "\u5b66\u4e60\u201c{label}\u201d\u65f6\uff0c\u6700\u9700\u8981\u638c\u63e1\u7684\u662f\u54ea\u4e00\u9879\uff1f",
    "\u4e0b\u5217\u54ea\u4e00\u9879\u6700\u7b26\u5408\u201c{label}\u201d\u7684\u8003\u67e5\u91cd\u70b9\uff1f",
    "\u5173\u4e8e\u201c{label}\u201d\u7684\u5178\u578b\u9898\uff0c\u6b63\u786e\u89e3\u9898\u601d\u8def\u662f\u54ea\u4e00\u9879\uff1f",
]

DATASET_TEMPLATES = [
    "\u5728{context}\u4e2d\uff0c\u672c\u9898\u8003\u67e5{label}\uff0c\u6838\u5fc3\u8981\u6c42\u662f{requirement}\u3002",
    "\u9488\u5bf9{context}\uff0c\u8fd9\u9053\u9898\u56f4\u7ed5{label}\u5c55\u5f00\uff0c\u5224\u65ad\u4f9d\u636e\u662f{requirement}\u3002",
    "\u5728{context}\u7684\u9057\u4f20\u4e0e\u8fdb\u5316\u6a21\u5757\u4e2d\uff0c{label}\u5e38\u8981\u6c42\u5b66\u751f{requirement}\u3002",
    "\u82e5{context}\u9898\u76ee\u51fa\u73b0{label}\u76f8\u5173\u60c5\u5883\uff0c\u5e94\u91cd\u70b9\u5173\u6ce8{requirement}\u3002",
    "\u672c\u9898\u6765\u81ea{context}\uff0c\u5c5e\u4e8e{label}\u77e5\u8bc6\u6a21\u5757\uff0c\u89e3\u9898\u65f6\u5e94\u80fd{requirement}\u3002",
]

DATASET_CONTEXTS = [
    "\u5355\u9879\u9009\u62e9\u9898",
    "\u591a\u9879\u5224\u65ad\u9898",
    "\u5b9e\u9a8c\u5206\u6790\u9898",
    "\u56fe\u8868\u8bc6\u522b\u9898",
    "\u9057\u4f20\u7cfb\u8c31\u9898",
    "\u6982\u5ff5\u8fa8\u6790\u9898",
    "\u6570\u636e\u63a8\u65ad\u9898",
    "\u60c5\u5883\u5e94\u7528\u9898",
    "\u590d\u4e60\u5de9\u56fa\u9898",
    "\u9519\u56e0\u5206\u6790\u9898",
    "\u6559\u6750\u57fa\u7840\u9898",
    "\u80fd\u529b\u63d0\u5347\u9898",
    "\u7efc\u5408\u8bad\u7ec3\u9898",
    "\u8003\u70b9\u5f52\u7eb3\u9898",
    "\u73b0\u8c61\u89e3\u91ca\u9898",
    "\u539f\u7406\u5e94\u7528\u9898",
    "\u7ed3\u8bba\u63a8\u7406\u9898",
    "\u8fc7\u7a0b\u6392\u5e8f\u9898",
    "\u5bf9\u7167\u5b9e\u9a8c\u9898",
    "\u6a21\u578b\u5efa\u6784\u9898",
]

COMMON_DISTRACTORS = [
    "\u53ea\u6839\u636e\u5355\u4e2a\u5173\u952e\u8bcd\u5224\u65ad",
    "\u5ffd\u7565\u9898\u76ee\u6761\u4ef6\u548c\u6570\u636e",
    "\u6df7\u6dc6\u4e0d\u540c\u77e5\u8bc6\u6a21\u5757\u7684\u9002\u7528\u8303\u56f4",
    "\u53ea\u8bb0\u5fc6\u7ed3\u8bba\uff0c\u4e0d\u5206\u6790\u73b0\u8c61",
]


def _normalize_requirement(text: str) -> str:
    return text.replace("\u4f1a", "").replace("\u638c\u63e1", "").replace("\u7406\u89e3", "").strip(" \uff0c\u3002")


def _option_text(label_id: int, answer: str) -> str:
    other_requirements = [
        item["core_requirement"] for item in KNOWLEDGE_POINTS if item["id"] != label_id
    ]
    distractors = COMMON_DISTRACTORS[:2] + other_requirements[label_id % len(other_requirements):]
    choices = [answer] + distractors[:3]
    return " ".join(
        f"{prefix}. {choice}" for prefix, choice in zip(["A", "B", "C", "D"], choices)
    )


def build_question_bank_rows(per_label: int = 20) -> list[dict]:
    rows = []
    for item in KNOWLEDGE_POINTS:
        answer_text = item["core_requirement"]
        analysis = f"\u8be5\u9898\u8003\u67e5{item['name']}\u3002\u6838\u5fc3\u8981\u6c42\u662f\uff1a{answer_text}\u3002"
        for idx in range(per_label):
            template = QUESTION_TEMPLATES[idx % len(QUESTION_TEMPLATES)]
            stem = template.format(label=item["name"])
            rows.append(
                {
                    "id": item["id"] * 1000 + idx + 1,
                    "stem": stem,
                    "options": _option_text(item["id"], answer_text),
                    "answer": "A",
                    "analysis": analysis,
                    "label_id": item["id"],
                    "difficulty": max(1, min(5, int(item["difficulty"]))),
                    "source": "generated_mvp_verified_concept",
                }
            )
    return rows


def build_model_dataset_rows(per_label: int = 100) -> list[dict]:
    rows = []
    for item in KNOWLEDGE_POINTS:
        requirement = _normalize_requirement(item["core_requirement"])
        for idx in range(per_label):
            template = DATASET_TEMPLATES[idx % len(DATASET_TEMPLATES)]
            context = DATASET_CONTEXTS[(idx // len(DATASET_TEMPLATES)) % len(DATASET_CONTEXTS)]
            rows.append(
                {
                    "text": template.format(
                        label=item["name"], requirement=requirement, context=context
                    ),
                    "label_id": item["id"],
                    "label_name": item["name"],
                    "source": "generated_mvp_verified_concept",
                }
            )
    return rows


def knowledge_point_rows() -> list[dict]:
    return [item.copy() for item in KNOWLEDGE_POINTS]
