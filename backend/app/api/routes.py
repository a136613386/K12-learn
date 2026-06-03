from flask import Blueprint, request

from app.repositories.prediction_repository import PredictionRepository
from app.repositories.wrong_question_repository import WrongQuestionRepository
from app.services.health_service import HealthService
from app.services.knowledge_service import KnowledgeService
from app.services.prediction_service import PredictionService
from app.services.stats_service import StatsService
from app.services.wrong_question_service import WrongQuestionService
from app.utils.responses import error_response, success_response


api_bp = Blueprint("api", __name__)


@api_bp.post("/wrong-questions/classify-and-recommend")
def classify_and_recommend_wrong_question():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return error_response("text is required", 400)

    result = WrongQuestionService().classify_and_recommend(text)
    return success_response(result)


@api_bp.post("/predict/knowledge-point")
def predict_knowledge_point():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return error_response("text is required", 400)

    result = PredictionService().predict(text)
    return success_response(result)


@api_bp.get("/knowledge-points")
def list_knowledge_points():
    return success_response(KnowledgeService().list_points())


@api_bp.get("/wrong-questions/recent")
def recent_wrong_questions():
    limit_raw = request.args.get("limit", "10")
    try:
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        return error_response("limit must be an integer", 400)

    return success_response(WrongQuestionRepository().recent(limit))


@api_bp.get("/predictions/recent")
def recent_predictions():
    limit_raw = request.args.get("limit", "10")
    try:
        limit = max(1, min(int(limit_raw), 50))
    except ValueError:
        return error_response("limit must be an integer", 400)

    return success_response(PredictionRepository().recent(limit))


@api_bp.get("/stats/overview")
def stats_overview():
    return success_response(StatsService().overview())


@api_bp.get("/health")
def health_check():
    return success_response(HealthService().status())
