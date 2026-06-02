from app import create_app


def test_predict_api_returns_result():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/v1/predict/knowledge-point",
        json={"text": "豌豆杂交实验出现3:1分离比，体现孟德尔遗传定律。"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["code"] == 0
    assert payload["data"]["knowledge_point_name"] == "孟德尔遗传定律"


def test_predict_api_requires_text():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/v1/predict/knowledge-point", json={"text": ""})

    assert response.status_code == 400
    assert response.get_json()["message"] == "text is required"
