from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.data import InteractionData


class Recommender(ABC):
    @abstractmethod
    def fit(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def score(
        self,
        *,
        user_id: str | None,
        interaction_history: list[str],
    ) -> dict[str, float]:
        raise NotImplementedError

    @abstractmethod
    def save(self, artifact_path: Path) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, artifact_path: Path) -> "Recommender":
        raise NotImplementedError


class InteractionRecommender(Recommender, ABC):
    @abstractmethod
    def fit(self, interactions: InteractionData) -> None:
        raise NotImplementedError