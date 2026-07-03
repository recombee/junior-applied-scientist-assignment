from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np

from app.models.base import Recommender


@dataclass
class ItemAttributeRecommender(Recommender):
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    item_ids: np.ndarray = field(default_factory=lambda: np.array([], dtype=object))
    item_embeddings: np.ndarray = field(default_factory=lambda: np.empty((0, 0), dtype=np.float32))

    def fit(self, item_texts: dict[str, str]) -> None:
        """Embed item attributes with a text embedding model and store normalized item vectors.

        TODO: load the configured text embedding model, encode item_texts, normalize
        embeddings for cosine similarity, and keep self.item_ids aligned with
        self.item_embeddings.

        Practical note: cap the model's max_seq_length (e.g. to 512 tokens) -
        some descriptions are long and unbounded batches can exhaust memory.
        See the README for model choice and expected runtimes on CPU vs GPU.
        """
        raise NotImplementedError("TODO: implement ItemAttributeRecommender.fit")

    def score(
        self,
        *,
        user_id: str | None,
        interaction_history: list[str],
    ) -> dict[str, float]:
        """Return content-based item scores from the user's interaction history.

        TODO: build a profile vector from the embeddings of interaction_history and
        return cosine-similarity scores for candidate items. user_id is accepted for
        interface consistency but does not need to be used by this model.
        """
        raise NotImplementedError("TODO: implement ItemAttributeRecommender.score")

    def save(self, artifact_path: Path) -> None:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model_name": self.model_name,
                "item_ids": self.item_ids,
                "item_embeddings": self.item_embeddings,
            },
            artifact_path,
        )

    @classmethod
    def load(cls, artifact_path: Path) -> "ItemAttributeRecommender":
        payload = joblib.load(artifact_path)
        return cls(
            model_name=payload["model_name"],
            item_ids=payload["item_ids"],
            item_embeddings=payload["item_embeddings"],
        )
