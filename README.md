# Take-Home Assignment: Junior Applied Scientist, Recommender Systems

Welcome, and thank you for taking the time to work on this assignment. We would like to see how you reason about recommender systems, how you structure machine learning code, and how you turn a model into a small service that can be called from an API.

We know your time is valuable. To help you focus on the core logic rather than boilerplate configuration, we have provided a skeleton repository containing the basic database setup and API structure. Concretely, it includes a prepared Flask application, database-loading utilities, request validation, and Docker setup. Your task is to fill in the model-specific parts marked with `TODO` comments. Please keep the existing API shape intact unless you have a strong reason to change it.

## About This Assignment

* **Position:** Junior Applied Scientist, Recommender Systems at Recombee.
* **Stage:** This is the take-home assignment for the second round of the interview process.
* **Scope:** The exercise is designed to be completed in a focused sitting. It is not meant to be an exhaustive production system - we care about how you reason and structure the code, not about polishing every detail.
* **What happens next:** You submit your solution before the interview (see [Submission](#submission)) and we discuss it together in the interview.

## A Note on AI Tools

Using AI coding assistants and agents is **not prohibited** - at Recombee you would use them every day, and we like that. For **this** assignment, however, we kindly ask you to **solve it yourself, without AI agents**.

The reason is the interview: we will go through your solution together and explore many "what would you do if..." situations - alternative modeling choices, trade-offs, edge cases, and how you would extend or debug the system. Those discussions are much more valuable (and enjoyable) when the reasoning behind the code is genuinely your own.

## Scenario

You are building a small recommendation service backed by a PostgreSQL database. The database is bundled into the Docker image (see [Dataset](#dataset) below) and contains user-item interactions and item attributes that can be used for content-based recommendations.

Your implementation should train and serve two recommenders:

1. An interaction-based recommender using SANSA.
2. An attribute-based recommender using a text embedding model.

Both recommenders should support optional whitelist and blacklist filters at request time.

## Dataset

The data is a subset of the [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/) dataset (McAuley Lab, UC San Diego), **Books** category.

It was prepared by applying a **20-core filter**: only users and items with at least 20 interactions each are kept (applied iteratively until every user and item satisfies the threshold). This removes the long tail of one-off users and rarely-reviewed books, leaving a dense subset that trains quickly and fits comfortably on a laptop. The resulting size is roughly **14k items** and **630k interactions**.

The original string identifiers are kept as natural keys: `item_id` is the book's Amazon `parent_asin` (a string that may contain letters, e.g. `006240749X`), and `user_id` is the reviewer's identifier.

Two tables are provided:

* **`items`** - one row per book, with attributes suitable for building an item text representation:
  `item_id`, `title`, `subtitle`, `author`, `description`, `categories`, `store`, `price`, `main_category`.
  Any attribute may be missing (`NULL`) for a given book.
* **`interactions`** - one row per review, treated as implicit feedback:
  `user_id`, `item_id`, `timestamp` (epoch milliseconds). There is no explicit `weight` column, so every interaction counts equally (the API query defaults it to `1.0`).


## Prerequisites

Before starting, please make sure you have:

* Docker. The assignment ships as a single self-contained image that runs PostgreSQL 15 and the Flask API together, so `docker build` and `docker run` are all you need.
* Enough free disk space for the Docker image, Python dependencies, model artifacts, and the text embedding model cache. We recommend at least **15 GB** free.
* Enough memory for sparse matrix operations and embedding generation. We recommend at least **8 GB** RAM (SANSA training peaks around 3 GB; embedding the catalog on CPU with the large default model peaks around 9 GB - use a smaller embedding model on CPU, see Task 2). If you use Docker Desktop (macOS/Windows), raise its VM memory limit accordingly, otherwise training is killed with exit code 137.

For local development without Docker, use Python 3.11 or newer and install dependencies from `requirements.txt`. Building `scikit-sparse` needs the SuiteSparse headers (`libsuitesparse-dev` on Debian/Ubuntu, `brew install suitesparse` on macOS, `suitesparse` on Arch). See [Local Development Against the Bundled Database](#6-local-development-against-the-bundled-database) for how to reach the data from your host.

## Repository Structure

```text
app/
  api.py                    Flask routes and error handling
  config.py                 Environment-based settings
  data.py                   PostgreSQL extraction helpers
  filtering.py              Shared whitelist/blacklist filtering
  schemas.py                Request validation
  services.py               Model loading and recommendation orchestration
  models/
    base.py                 Shared recommender interface
    sansa.py                TODO: implement SANSA training and scoring
    item_attribute.py       TODO: implement text embedding model
scripts/
  train_models.py           Training entry point
  load_local_db.sh          Load the CSVs into your own PostgreSQL (local dev)
db/
  init_db.sql               Database schema
  items.csv.gz              Item data, loaded into the image at build time
  interactions.csv.gz       Interaction data, loaded into the image at build time
docker-entrypoint.sh        Starts PostgreSQL, then the API
Dockerfile                  Single image: PostgreSQL 15 + the Flask API
requirements.txt            Python dependencies
```

## Your Tasks

### 1. Implement the SANSA Model

Fill in `app/models/sansa.py`.

The model should:

* Train from the sparse user-item interaction matrix produced by `app/data.py`.
* Store the information needed for recommendation in a serializable artifact.
* Score candidate items for a request containing a `user_id` and/or an `interaction_history`.
* Handle users that are not present in the training data by using the supplied interaction history when possible.

You may choose reasonable hyperparameters. Please keep the implementation readable and add a short note in the code or README if you make an important modeling choice.

You may use the official [`sansa` package](https://github.com/glami/sansa) (already in `requirements.txt`) or implement the algorithm yourself - either way, be ready to explain how the training works and where the expensive operations are.

### 2. Implement the Attribute Text Embedding Model

Fill in `app/models/item_attribute.py`.

The model should:

* Build item text representations from the item attributes loaded from PostgreSQL.
* Use a text embedding model to embed item attributes. `Qwen/Qwen3-Embedding-0.6B` is a good default **on a GPU** (including a laptop GPU); **on CPU** we suggest a smaller model such as `sentence-transformers/all-MiniLM-L6-v2`. The model is selected via `EMBEDDING_MODEL_NAME`.
* Create a user/profile representation from `interaction_history`.
* Recommend items whose attribute embeddings are most similar to the profile.
* Save and load its artifact so the Flask API can serve it without retraining on every request.

If you need to adapt the exact item text construction to the provided data schema, keep the change small and document it briefly.

### 3. Serve Recommendations Through the Prepared API

The Flask API is already wired for two endpoints:

* `POST /recommend/sansa`
* `POST /recommend/attributes`

Both endpoints accept the same JSON payload:

```json
{
  "user_id": "AFW2PDT3AMT4X3PYQG7FJZH5FXFA",
  "interaction_history": ["006240749X", "B08F4GYM8W", "0385349521"],
  "top_k": 5,
  "whitelist": ["B00BEK6ZR2", "0316055433", "0007149824", "0060004878"],
  "blacklist": ["0385349521"]
}
```

All IDs in these examples exist in the bundled dataset, and the whitelist items are books this user has *not* interacted with, so a correct solution can return every one of them.

Fields:

* `user_id`: user identifier. It may be unknown to the trained model.
* `interaction_history`: item IDs that describe the user's recent or known preferences.
* `top_k`: number of recommendations to return. Defaults to `10`.
* `whitelist`: optional item IDs that recommendations must be selected from.
* `blacklist`: optional item IDs that must not be recommended. The blacklist takes precedence over the whitelist.

Expected response (the whitelist items minus the blacklist, ranked by your model - the exact order depends on your implementation):

```json
{
  "model": "sansa",
  "recommendations": ["0060004878", "B00BEK6ZR2", "0316055433", "0007149824"]
}
```

The shared filtering logic lives in `app/filtering.py`. You can adjust it if needed, but the endpoints should continue to support both whitelist and blacklist.

### 4. Build and Run the Container

The image bundles PostgreSQL 15 (with the assignment data already loaded) and the Flask API. Build it once, then run it:

```bash
docker build -t recsys-assignment .
docker run --rm -p 8000:8000 --name recsys-assignment recsys-assignment
```

The API is available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

### 5. Train and Save Model Artifacts

After implementing the model TODOs, train inside the running container:

```bash
docker exec -it recsys-assignment python scripts/train_models.py --models sansa attributes
```

Artifacts are written to `ARTIFACT_DIR` (default `/app/artifacts`) inside the container. Models are loaded lazily on the first request and reloaded automatically when the artifact file changes, so you can train (and retrain) and then call the API without restarting the container. To keep artifacts - and the downloaded embedding model - on your host across container removals, mount volumes when you run:

```bash
docker run --rm -p 8000:8000 --name recsys-assignment \
  -v "$(pwd)/artifacts:/app/artifacts" \
  -v hf-cache:/root/.cache/huggingface \
  recsys-assignment
```

As a rough guide, on a modern desktop CPU, SANSA trains in ~2-3 minutes. Embedding the catalog with `Qwen/Qwen3-Embedding-0.6B` takes ~10 minutes on a consumer GPU but several hours CPU-only - hence the smaller-model suggestion in Task 2. It is also fine to train the embedding artifact outside the container (e.g. on a GPU machine) into the mounted `artifacts/` directory.

Example request (all IDs exist in the bundled dataset):

```bash
curl -X POST http://localhost:8000/recommend/sansa \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "AFW2PDT3AMT4X3PYQG7FJZH5FXFA", "interaction_history": ["006240749X", "B08F4GYM8W", "0385349521"], "top_k": 5, "blacklist": ["0385349521"]}'
```

### 6. Local Development Against the Bundled Database

You do not have to develop inside the container. Two supported options:

**Option A - publish the container's PostgreSQL port.** The bundled Postgres accepts password-authenticated connections from outside the container, so simply publish port 5432 alongside the API:

```bash
docker run --rm -p 8000:8000 -p 5432:5432 --name recsys-assignment recsys-assignment

# then, on the host:
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://assignment:assignment@localhost:5432/recsys"
python scripts/train_models.py --models sansa attributes
flask --app run:app run --host 0.0.0.0 --port 8000
```

**Option B - load the data into your own PostgreSQL.** If you already run Postgres locally, `scripts/load_local_db.sh` creates the schema and loads both CSVs into an existing database (defaults to `postgresql://assignment:assignment@localhost:5432/recsys`).

To iterate on code inside the container without rebuilding the image, bind-mount the source directory: add `-v "$(pwd)/app:/app/app"` (and `-v "$(pwd)/scripts:/app/scripts"`) to `docker run`.

## What We Look For

* Correctness of the SANSA and attribute-based recommendation logic.
* Clear, maintainable Python code that fits the prepared structure.
* How you use Python: idiomatic, clean, and self-explaining code that is still written with efficiency in mind.
* Sensible handling of unknown users, empty histories, missing item attributes, and small candidate sets after filtering.
* Awareness of performance trade-offs, especially sparse matrix operations and embedding storage.
* A short explanation of any assumptions you made.

## Follow-Up Discussion

If you continue to the next round, we will review the solution together. Please be ready to discuss:

1. How your SANSA implementation works and where the expensive operations are.
2. How the text embedding recommender behaves for users with short or noisy histories.
3. What happens if the item catalog grows by orders of magnitude.
4. How you would evaluate these models offline.
5. How you would retrain and deploy the models as new interactions arrive.

## Submission

We use a fork-based workflow so that your solution stays private to you and the reviewers.

1. **Fork this repository** to your own account.
2. **Make your fork private and standalone.** In your fork, go to **Settings -> General**:
   * Under **Advanced -> Remove fork relationship**, remove the link to the original project so your work is not visible to other candidates through the upstream repository.
   * Under **Visibility, project features, permissions**, set the visibility to **Private**.
3. **Grant reviewer access.** In **Project information -> Members**, add the following users as members (Developer role is sufficient):
   * [@Kasape](https://github.com/Kasape)
   * [@dbohunek](https://github.com/dbohunek)
4. **Commit your work to your fork** and push it before the deadline below.

Include any README notes needed to run your solution and to explain the assumptions you made. Do not include database dumps or large downloaded model files unless instructed by the complementary materials.

### Deadline

The interview date is arranged over email. Please **submit your solution at least 24 hours before the scheduled interview** so we have time to review it. The assignment is discussed in depth during the interview, so be ready to walk through your code, your modeling choices, and the trade-offs you made.

Good luck, and enjoy the assignment.
