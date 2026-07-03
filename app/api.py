from __future__ import annotations

from flask import Flask, jsonify, request

from app.config import Settings
from app.schemas import RequestValidationError, RecommendationRequest
from app.services import ModelArtifactMissingError, RecommendationService


def create_app(
    settings: Settings | None = None,
    service: RecommendationService | None = None,
) -> Flask:
    app = Flask(__name__)
    resolved_settings = settings or Settings.from_env()
    recommendation_service = service or RecommendationService(resolved_settings)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/recommend/sansa")
    def recommend_sansa():
        return _recommend("sansa", resolved_settings, recommendation_service)

    @app.post("/recommend/attributes")
    def recommend_attributes():
        return _recommend("attributes", resolved_settings, recommendation_service)

    return app


def _recommend(
    model_name: str,
    settings: Settings,
    service: RecommendationService,
):
    try:
        payload = request.get_json(silent=True)
        recommendation_request = RecommendationRequest.from_payload(payload, settings)
        recommendations = service.recommend(model_name, recommendation_request)
    except RequestValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except ModelArtifactMissingError as exc:
        return jsonify({"error": str(exc)}), 503
    except NotImplementedError as exc:
        return jsonify({"error": str(exc)}), 501

    return jsonify({"model": model_name, "recommendations": recommendations})