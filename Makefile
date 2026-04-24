.PHONY: up down restart rebuild rebuild-nocache logs \
        logs-backend logs-frontend logs-nginx \
        shell-backend shell-frontend \
        dev-backend dev-frontend \
        install install-backend install-frontend \
        dataset train test-model \
        seed seed-local db-reset schema-reset \
        clean clean-volumes help

# ── Docker Compose ────────────────────────────────────────────────────────────

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

rebuild:
	docker-compose up --build -d

rebuild-nocache:
	docker-compose down && docker-compose build --no-cache && docker-compose up -d

# ── Logs ─────────────────────────────────────────────────────────────────────

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-nginx:
	docker-compose logs -f nginx

# ── Shells ────────────────────────────────────────────────────────────────────

shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

# ── Local dev (no Docker) ─────────────────────────────────────────────────────

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── ML / Trainer ─────────────────────────────────────────────────────────────

dataset:
	cd trainer && python import_dataset.py

train:
	cd trainer && python train.py

test-model:
	cd trainer && python test.py

# ── Seeding ───────────────────────────────────────────────────────────────────

seed:
	docker-compose exec backend python seed.py

seed-local:
	cd backend && python seed.py

db-reset:
	@echo "Clearing all dogs from PostgreSQL and ChromaDB..."
	docker-compose exec backend python -c "\
import os; \
from database import SessionLocal, Dog, DogPhoto, Message; \
import chromadb; \
db = SessionLocal(); \
db.query(Message).delete(); \
db.query(DogPhoto).delete(); \
db.query(Dog).delete(); \
db.commit(); \
db.close(); \
client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', '/chroma_data')); \
client.delete_collection('dogs'); \
client.get_or_create_collection('dogs'); \
print('Done.')"

schema-reset:
	@echo "Dropping postgres volume and recreating schema from scratch..."
	docker-compose down -v
	docker-compose up -d
	@echo "Schema reset complete. Run 'make seed' to repopulate sample data."

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	docker-compose down --rmi local

clean-volumes:
	docker-compose down -v

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  Pawfound — available targets"
	@echo ""
	@echo "  Docker  (app at http://localhost)"
	@echo "    make up            Start all services"
	@echo "    make rebuild       Build images and start all services"
	@echo "    make down          Stop all services"
	@echo "    make restart       Restart all services (no rebuild)"
	@echo ""
	@echo "  Logs"
	@echo "    make logs          Tail all logs"
	@echo "    make logs-backend  Tail backend logs"
	@echo "    make logs-frontend Tail frontend logs"
	@echo "    make logs-nginx    Tail nginx logs"
	@echo ""
	@echo "  Shells"
	@echo "    make shell-backend   Open shell in backend container"
	@echo "    make shell-frontend  Open shell in frontend container"
	@echo ""
	@echo "  Local dev (no Docker)"
	@echo "    make install         Install all dependencies"
	@echo "    make dev-backend     uvicorn --reload on :8000"
	@echo "    make dev-frontend    Vite dev server on :5173"
	@echo ""
	@echo "  ML"
	@echo "    make dataset       Download Stanford Dogs dataset"
	@echo "    make train         Fine-tune EfficientNetV2"
	@echo "    make test-model    Run embedding similarity test"
	@echo ""
	@echo "  Seeding"
	@echo "    make seed          Seed DB via backend container (Docker)"
	@echo "    make seed-local    Seed DB via local backend on :8000"
	@echo "    make db-reset      Clear all dogs (keeps tables/schema)"
	@echo "    make schema-reset  Drop postgres volume + recreate schema (WIPES ALL DATA)"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean         Stop + remove local images"
	@echo "    make clean-volumes Stop + remove volumes (clears ChromaDB)"
	@echo ""
