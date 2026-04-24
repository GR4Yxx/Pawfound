# Pawfound

A full-stack web app that uses computer vision to match photos of lost and found dogs, helping reunite pets with their families.

Upload a photo → AI extracts a visual embedding → cosine similarity search across all reports → ranked matches in seconds.

![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi) ![PyTorch](https://img.shields.io/badge/PyTorch-EfficientNetV2-EE4C2C?logo=pytorch) ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## How it works

1. A user reports a lost or found dog with photos and metadata
2. Each photo is passed through a fine-tuned **EfficientNetV2-S** model to produce a 1280-dimensional visual embedding
3. Embeddings are stored in **ChromaDB** with cosine similarity indexing
4. When a new report comes in, the backend automatically searches for visual matches above a similarity threshold and delivers **in-app inbox notifications** to matching dog owners
5. Users can also manually scan any photo against all reports via the Browse page

---

## Tech Stack

| Layer      | Technology                                              |
|------------|---------------------------------------------------------|
| ML Model   | EfficientNetV2-S (PyTorch), fine-tuned on Stanford Dogs |
| Vector DB  | ChromaDB — cosine similarity, 1280-dim embeddings       |
| Backend    | FastAPI, SQLAlchemy, PostgreSQL, Python 3.11            |
| Auth       | JWT (httpOnly cookies) + bcrypt                         |
| Frontend   | Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS v3   |
| Infra      | Docker Compose, nginx reverse proxy                     |

---

## Project Structure

```
Pawfound/
├── backend/
│   ├── main.py          # All API routes
│   ├── auth.py          # JWT auth, login/register endpoints
│   ├── database.py      # SQLAlchemy models (User, Dog, DogPhoto, Message)
│   ├── embedder.py      # EfficientNetV2-S inference — only file that touches the model
│   ├── seed.py          # Seed script: inserts demo dogs into Postgres + ChromaDB
│   └── Dockerfile
│
├── frontend/
│   └── src/
│       ├── views/       # Page components (Home, Browse, Report, Profile, Inbox, ...)
│       ├── components/  # NavBar, DogCard, AppFooter, MapPicker, PhotoGallery
│       ├── stores/      # Pinia stores: auth, inbox (unread count), matchQueue
│       ├── api.ts       # Typed fetch wrappers for all backend endpoints
│       └── types.ts     # Shared TypeScript interfaces
│
├── trainer/
│   ├── train.py         # Fine-tune EfficientNetV2-S on Stanford Dogs dataset
│   ├── import_dataset.py# Downloads and prepares the dataset
│   └── dog_model.pth    # Trained weights (not committed — see below)
│
├── nginx/
│   └── nginx.dev.conf   # Reverse proxy: /api → FastAPI, / → Vite dev server
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Trained model weights (see [Getting the model](#getting-the-model) below)

### Getting the model

The app needs `backend/dog_model.pth` — an EfficientNetV2-S fine-tuned on Stanford Dogs. You have two options:

**Option A — Train it yourself** (~1 hour on a GPU, 15 min on CPU for a rough model):
```bash
make dataset   # download Stanford Dogs dataset (~750 MB)
make train     # fine-tune EfficientNetV2-S, saves to trainer/dog_model.pth
cp trainer/dog_model.pth backend/dog_model.pth
```

**Option B — Download pre-trained weights:**
If weights are provided separately (e.g. a release asset or shared link), place the file at `backend/dog_model.pth`.

> Without `dog_model.pth` the backend will start but crash on the first `/report`, `/match`, or `/identify` request.

---

### 1. Clone and configure

```bash
git clone <repo-url>
cd Pawfound
cp .env.example .env
```

Open `.env` and set a real JWT secret — everything else works as-is for local dev:

```bash
# generate a secure secret:
python -c "import secrets; print(secrets.token_hex(32))"
# paste the output as JWT_SECRET in .env
```

### 2. Build and start

```bash
make rebuild   # builds images + starts all services
```

Or with plain Docker Compose:
```bash
docker compose up --build
```

First build takes 5–10 minutes (downloads PyTorch). Subsequent builds are fast thanks to the layered Dockerfile.

| URL | What |
|-----|------|
| http://localhost | App (via nginx) |
| http://localhost/api/docs | Swagger UI |
| http://localhost:8000/docs | Backend direct |

### 3. Seed demo data

```bash
make seed
```

Inserts ~30 dog reports from the Stanford Dogs dataset and creates a demo account:

```
Email:    demo@pawfound.app
Password: demo1234
```

### 4. Common commands

```bash
make logs          # tail all container logs
make logs-backend  # backend only
make restart       # restart without rebuilding
make db-reset      # wipe all dog data, keep schema
make schema-reset  # wipe everything including Postgres volume
make down          # stop all containers
```

Run `make help` for the full list.

---

## API Endpoints

### Auth
| Method | Path              | Auth | Description              |
|--------|-------------------|------|--------------------------|
| POST   | `/auth/register`  | —    | Create account           |
| POST   | `/auth/login`     | —    | Login, sets JWT cookie   |
| POST   | `/auth/logout`    | —    | Clear JWT cookie         |
| GET    | `/auth/me`        | ✓    | Get current user         |

### Dogs
| Method | Path                   | Auth | Description                              |
|--------|------------------------|------|------------------------------------------|
| POST   | `/report`              | ✓    | Report a lost/found dog (multipart)      |
| GET    | `/dogs`                | —    | List all reports (paginated)             |
| GET    | `/dog/{id}`            | —    | Get a single dog by Postgres UUID or chroma_id |
| POST   | `/match`               | —    | Find top-5 visual matches for an image   |
| PATCH  | `/dog/{id}/status`     | ✓    | Mark as active or reunited               |
| GET    | `/users/me/dogs`       | ✓    | List the current user's reports          |
| GET    | `/image/{chroma_id}`   | —    | Serve a dog photo (cached)               |
| POST   | `/identify`            | —    | Top-3 breed predictions for an image     |

### Messaging
| Method | Path                        | Auth | Description                         |
|--------|-----------------------------|------|-------------------------------------|
| POST   | `/messages`                 | ✓    | Send a message about a dog          |
| GET    | `/messages/inbox`           | ✓    | Get inbox threads                   |
| GET    | `/messages/thread/{dog_id}` | ✓    | Get all messages for a dog thread   |
| GET    | `/messages/unread-count`    | ✓    | Get unread message count            |

---

## Key Design Decisions

### Dual ID system
Dogs have two IDs that serve different purposes:
- **Postgres UUID** (`Dog.id`) — used by `/dog/{id}`, `/report` response, ownership checks
- **ChromaDB chroma_id** (`Dog.chroma_id`) — used by `/dogs` list, `/match`, messaging endpoints

The `GET /dog/{id}` endpoint accepts either — it tries Postgres UUID first, then falls back to chroma_id lookup.

### Images stored in ChromaDB metadata
Images are base64-encoded and stored alongside embeddings in ChromaDB metadata. This avoids a separate file store for a single-server setup. The `/image/{chroma_id}` endpoint decodes and serves them with aggressive cache headers — list endpoints return URLs, not inline data URIs, keeping responses small.

### Auto-matching on report
When a new dog is reported, `_notify_potential_matches` runs as a FastAPI `BackgroundTask`. It queries ChromaDB for visual matches above `NOTIFY_THRESHOLD` (default 0.45) and writes system `Message` rows to the matched dog owner's inbox thread. These appear as AI alert cards with a direct link to the potential match.

### System messages
`Message.sender_id` is nullable. `Message.is_system = True` marks automated match notifications from the backend — these are rendered differently in the inbox UI (styled alert card rather than a chat bubble).

---

## Training the Model

The model is EfficientNetV2-S fine-tuned on the [Stanford Dogs Dataset](http://vision.stanford.edu/aditya86/ImageNetDogs/) (120 breeds, ~20,000 images). The classifier head is replaced and the full network is fine-tuned for breed classification. At inference, the penultimate layer's 1280-dim output is used as the visual embedding — not the breed prediction itself.

```bash
cd trainer
python import_dataset.py   # Download Stanford Dogs dataset (~750 MB)
python train.py            # Fine-tune for 10 epochs, saves best checkpoint
```

The weights are saved to `trainer/dog_model.pth`. Copy to `backend/dog_model.pth` before building.

To swap the embedding model entirely, only `backend/embedder.py` needs to change — it exposes a single `get_embedding(image_bytes: bytes) -> list[float]` function.

---

## Environment Variables

| Variable             | Required | Default                        | Description                          |
|----------------------|----------|--------------------------------|--------------------------------------|
| `JWT_SECRET`         | ✓        | —                              | Secret for signing JWT tokens        |
| `DB_URL`             | ✓        | —                              | PostgreSQL connection string         |
| `CHROMA_PATH`        | —        | `/chroma_data`                 | ChromaDB persistence directory       |
| `SIMILARITY_THRESHOLD` | —      | `0.45`                         | Minimum similarity for match results |
| `NOTIFY_THRESHOLD`   | —        | `0.45`                         | Minimum similarity for inbox alerts  |
| `SMTP_HOST`          | —        | `` (disabled)                  | SMTP server for email notifications  |
| `SMTP_USER`          | —        | —                              | SMTP username                        |
| `SMTP_PASS`          | —        | —                              | SMTP password                        |
| `APP_BASE_URL`       | —        | `http://localhost`             | Used in email notification links     |
| `CORS_ORIGINS`       | —        | `http://localhost`             | Comma-separated allowed origins      |

---

## .gitignore Notes

Make sure these are excluded before pushing:

```
.env
backend/dog_model.pth       # large binary, distribute separately
trainer/data/               # Stanford Dogs dataset (~750 MB)
frontend/node_modules/
**/__pycache__/
*.pyc
chroma_data/
```
