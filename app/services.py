from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.filtering import apply_candidate_filters
from app.models.base import Recommender
from app.models.item_attribute import ItemAttributeRecommender
from app.models.sansa import SANSARecommender
from app.schemas import RecommendationRequest


class ModelArtifactMissingError(FileNotFoundError):
    pass


class RecommendationService:
    def __init__(self, settings: Settings, models: dict[str, Recommender] | None = None):
        self.settings = settings
        self._models = models or {}
        # Modification time of the artifact each cached model was loaded from,
        # so a retrain is picked up without restarting the API.
        self._artifact_mtimes: dict[str, float] = {}

    def recommend(self, model_name: str, request: RecommendationRequest) -> list[str]:
        model = self._get_model(model_name)
        scores = model.score(
            user_id=request.user_id,
            interaction_history=request.interaction_history,
        )
        return apply_candidate_filters(
            scores,
            top_k=request.top_k,
            whitelist=request.whitelist,
            blacklist=request.blacklist,
            seen_items=request.interaction_history,
        )

    def _get_model(self, model_name: str) -> Recommender:
        if model_name == "sansa":
            model_class: type[Recommender] = SANSARecommender
            artifact_path = self.settings.sansa_artifact_path
        elif model_name == "attributes":
            model_class = ItemAttributeRecommender
            artifact_path = self.settings.attributes_artifact_path
        elif model_name in self._models:  # injected models (e.g. test doubles)
            return self._models[model_name]
        else:
            raise ValueError(f"Unknown model: {model_name}")

        if model_name in self._models and not self._artifact_changed(model_name, artifact_path):
            return self._models[model_name]

        model = self._load_model(model_name, model_class, artifact_path)
        self._models[model_name] = model
        self._artifact_mtimes[model_name] = artifact_path.stat().st_mtime
        return model

    def _artifact_changed(self, model_name: str, artifact_path: Path) -> bool:
        loaded_mtime = self._artifact_mtimes.get(model_name)
        if loaded_mtime is None:  # injected directly, never reload
            return False
        return artifact_path.exists() and artifact_path.stat().st_mtime > loaded_mtime

    @staticmethod
    def _load_model(model_name: str, model_class: type[Recommender], artifact_path: Path) -> Recommender:
        if not artifact_path.exists():
            raise ModelArtifactMissingError(
                f"Model artifact for '{model_name}' not found at {artifact_path}. "
                "Run scripts/train_models.py after implementing the model TODOs."
            )
        return model_class.load(artifact_path)
