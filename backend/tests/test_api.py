from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


MENGDEER_TEXT = "\u8c4c\u8c46\u6742\u4ea4\u5b9e\u9a8c\u51fa\u73b03:1\u5206\u79bb\u6bd4\uff0c\u4f53\u73b0\u5b5f\u5fb7\u5c14\u9057\u4f20\u5b9a\u5f8b\u3002"
MENGDEER_LABEL = "\u5b5f\u5fb7\u5c14\u9057\u4f20\u5b9a\u5f8b"


def test_wrong_question_api_returns_classification_and_recommendations():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/v1/wrong-questions/classify-and-recommend",
        json={"text": MENGDEER_TEXT},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["code"] == 0
    data = payload["data"]
    assert data["classification"]["knowledge_point_name"] == MENGDEER_LABEL
    assert data["recommendation_count"] == 5
    assert len(data["recommended_questions"]) == 5
    assert data["recommended_questions"][0]["answer"]


def test_wrong_question_api_requires_text():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/v1/wrong-questions/classify-and-recommend",
        json={"text": ""},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "text is required"


def test_legacy_predict_api_still_returns_result():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/v1/predict/knowledge-point",
        json={"text": MENGDEER_TEXT},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["code"] == 0
    assert payload["data"]["knowledge_point_name"] == MENGDEER_LABEL
