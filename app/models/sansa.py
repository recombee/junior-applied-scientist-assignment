from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.data import InteractionData
from app.models.base import InteractionRecommender


@dataclass
class SANSARecommender(InteractionRecommender):
    item_ids: np.ndarray = field(default_factory=lambda: np.array([], dtype=object))
    user_ids: np.ndarray = field(default_factory=lambda: np.array([], dtype=object))
    state: dict[str, Any] = field(default_factory=dict)

    def fit(self, interactions: InteractionData) -> None:
        """Train SANSA from a sparse user-item matrix.

        TODO: implement the SANSA training procedure. Store every object needed for
        scoring in self.state, and keep item_ids/user_ids aligned with the matrix.

        You may use the official `sansa` package (already in requirements.txt,
        see https://github.com/glami/sansa) or implement the algorithm yourself
        - either way, be ready to explain how it works.
        """
        self.item_ids = interactions.item_ids
        self.user_ids = interactions.user_ids
        raise NotImplementedError("TODO: implement SANSARecommender.fit")

    def score(
        self,
        *,
        user_id: str | None,
        interaction_history: list[str],
    ) -> dict[str, float]:
        """Return item scores for the provided user context.

        TODO: use the trained SANSA state to score all candidate items. Prefer the
        trained user representation when user_id is known, and fall back to the
        supplied interaction_history for unknown users.
        """
        raise NotImplementedError("TODO: implement SANSARecommender.score")

    def save(self, artifact_path: Path) -> None:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "item_ids": self.item_ids,
                "user_ids": self.user_ids,
                "state": self.state,
            },
            artifact_path,
        )

    @classmethod
    def load(cls, artifact_path: Path) -> "SANSARecommender":
        payload = joblib.load(artifact_path)
        return cls(
            item_ids=payload["item_ids"],
            user_ids=payload["user_ids"],
            state=payload["state"],
        )
