from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Support `python scripts/train_models.py`: Python puts scripts/ on sys.path,
# not the repo root, so make the `app` package importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.data import create_database_engine, load_interactions, load_item_texts  # noqa: E402
from app.models.item_attribute import ItemAttributeRecommender  # noqa: E402
from app.models.sansa import SANSARecommender  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train recommender assignment models")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("sansa", "attributes"),
        default=("sansa", "attributes"),
        help="Models to train",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    engine = create_database_engine(settings)

    if "sansa" in args.models:
        interactions = load_interactions(engine, settings)
        sansa = SANSARecommender()
        sansa.fit(interactions)
        sansa.save(settings.sansa_artifact_path)

    if "attributes" in args.models:
        item_texts = load_item_texts(engine, settings)
        attributes = ItemAttributeRecommender(model_name=settings.embedding_model_name)
        attributes.fit(item_texts)
        attributes.save(settings.attributes_artifact_path)


if __name__ == "__main__":
    main()