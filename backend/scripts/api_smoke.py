import json
import urllib.request


BASE_URL = "http://127.0.0.1:8000/api/v1"


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    health = get_json("/health")
    print("health:", json.dumps(health, ensure_ascii=False))
    result = post_json(
        "/wrong-questions/classify-and-recommend",
        {"text": "豌豆杂交实验中F2出现3:1分离比，说明显隐性和基因型关系。"},
    )
    print("wrong-question:", json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
