-- Schema for the take-home assignment database (Amazon Reviews 2023 - Books).
--
-- Two tables back the recommenders:
--   * items        - book attributes, used by the text-embedding recommender
--   * interactions - user/item reviews, used by the SANSA recommender
--
-- Populated from the CSVs produced by data_prep/prepare_amazon_data.py:
--   items.csv         -> items
--   interactions.csv  -> interactions
--
-- IDs are the natural Amazon keys: item_id is the `parent_asin` (a string that
-- may contain letters, e.g. 006240749X) and user_id is the review user string.
--
-- The API reads these through the queries in app/config.py:
--   INTERACTIONS_SQL = "select user_id, item_id, coalesce(weight, 1.0) as weight from interactions"
--   ITEMS_SQL        = "select * from items"
-- Every non-`item_id` column of `items` is concatenated into the text that gets
-- embedded, so add or remove attribute columns here to change the item text.

CREATE TABLE IF NOT EXISTS items (
    item_id       TEXT PRIMARY KEY,
    title         TEXT,
    subtitle      TEXT,
    author        TEXT,
    description   TEXT,
    categories    TEXT,
    store         TEXT,
    price         NUMERIC,
    main_category TEXT
);

-- `weight` is not present in the CSV (interactions are implicit feedback); it
-- stays NULL and the API query coalesces it to 1.0. `timestamp` is the review
-- time in epoch milliseconds.
CREATE TABLE IF NOT EXISTS interactions (
    user_id   TEXT   NOT NULL,
    item_id   TEXT   NOT NULL,
    timestamp BIGINT,
    weight    REAL
);

CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions (user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_item ON interactions (item_id);
