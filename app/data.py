from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import Settings


@dataclass(frozen=True)
class InteractionData:
    matrix: sparse.csr_matrix
    user_ids: np.ndarray
    item_ids: np.ndarray


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url)


def load_interactions(engine: Engine, settings: Settings) -> InteractionData:
    rows = _fetch_rows(engine, settings.interactions_sql)
    if not rows:
        return InteractionData(
            matrix=sparse.csr_matrix((0, 0), dtype=np.float32),
            user_ids=np.array([], dtype=object),
            item_ids=np.array([], dtype=object),
        )

    raw_user_ids = np.array([row["user_id"] for row in rows])
    raw_item_ids = np.array([row["item_id"] for row in rows])
    weights = np.array([row.get("weight", 1.0) or 1.0 for row in rows], dtype=np.float32)

    user_ids, user_indices = np.unique(raw_user_ids, return_inverse=True)
    item_ids, item_indices = np.unique(raw_item_ids, return_inverse=True)

    matrix = sparse.csr_matrix(
        (weights, (user_indices, item_indices)),
        shape=(len(user_ids), len(item_ids)),
        dtype=np.float32,
    )
    return InteractionData(matrix=matrix, user_ids=user_ids, item_ids=item_ids)


def load_item_texts(engine: Engine, settings: Settings) -> dict[str, str]:
    rows = _fetch_rows(engine, settings.items_sql)
    item_texts: dict[str, str] = {}

    for row in rows:
        if "item_id" not in row:
            raise ValueError("items_sql must return an item_id column")
        item_id = row["item_id"]
        parts = [str(value) for key, value in row.items() if key != "item_id" and value]
        item_texts[item_id] = " | ".join(parts)

    return item_texts


def _fetch_rows(engine: Engine, sql: str) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        result = connection.execute(text(sql))
        return [dict(row) for row in result.mappings()]