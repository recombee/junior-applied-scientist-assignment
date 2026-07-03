from app.api import create_app
from app.config import Settings


class DummyService:
    def recommend(self, model_name, request):
        return ["006240749X", "B08F4GYM8W"][: request.top_k]


def test_recommend_endpoint_returns_recommendations(tmp_path):
    settings = Settings.from_env()
    settings = Settings(
        database_url=settings.database_url,
        artifact_dir=tmp_path,
        embedding_model_name=settings.embedding_model_name,
        default_top_k=settings.default_top_k,
        max_top_k=settings.max_top_k,
        interactions_sql=settings.interactions_sql,
        items_sql=settings.items_sql,
    )
    app = create_app(settings=settings, service=DummyService())

    response = app.test_client().post(
        "/recommend/sansa",
        json={
            "user_id": "AFW2PDT3AMT4X3PYQG7FJZH5FXFA",
            "interaction_history": ["006240749X", "B08F4GYM8W"],
            "top_k": 1,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"model": "sansa", "recommendations": ["006240749X"]}


def test_recommend_endpoint_validates_payload(tmp_path):
    settings = Settings.from_env()
    app = create_app(settings=settings, service=DummyService())

    response = app.test_client().post("/recommend/sansa", json={"top_k": 1})

    assert response.status_code == 400