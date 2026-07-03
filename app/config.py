from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    artifact_dir: Path
    embedding_model_name: str
    default_top_k: int
    max_top_k: int
    interactions_sql: str
    items_sql: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://assignment:assignment@localhost:5432/recsys",
            ),
            artifact_dir=Path(os.getenv("ARTIFACT_DIR", "artifacts")),
            embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-0.6B"),
            default_top_k=int(os.getenv("DEFAULT_TOP_K", "10")),
            max_top_k=int(os.getenv("MAX_TOP_K", "100")),
            interactions_sql=os.getenv(
                "INTERACTIONS_SQL",
                "select user_id, item_id, coalesce(weight, 1.0) as weight from interactions",
            ),
            items_sql=os.getenv("ITEMS_SQL", "select * from items"),
        )

    @property
    def sansa_artifact_path(self) -> Path:
        return self.artifact_dir / "sansa.joblib"

    @property
    def attributes_artifact_path(self) -> Path:
        return self.artifact_dir / "item_attributes.joblib"