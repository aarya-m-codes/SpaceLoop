.PHONY: help install dev test test-backend test-frontend build clean docker-up docker-down lint seed init-db

help:
	@echo "SpaceLoop Development & Operational Commands:"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make dev             Start backend and frontend development servers"
	@echo "  make test            Run all test suites via pytest"
	@echo "  make test-backend    Run Python test suite"
	@echo "  make test-frontend   Run frontend production build verification"
	@echo "  make build           Build production frontend assets (frontend/dist)"
	@echo "  make lint            Run linters across codebase"
	@echo "  make init-db         Initialize database schema"
	@echo "  make seed            Seed database with mock listings and users"
	@echo "  make docker-up       Start multi-service Docker containers"
	@echo "  make docker-down     Stop Docker containers"
	@echo "  make clean           Remove cached files and build artifacts"

install:
	pip install -r backend/requirements.txt
	npm ci --prefix frontend

dev:
	@echo "Starting development environment..."
	npm run dev --prefix frontend & python backend/run.py

test: test-backend

test-backend:
	python -m pytest

test-frontend:
	npm run build --prefix frontend

build:
	npm run build --prefix frontend

init-db:
	python -m flask --app backend.run:app init-db

seed:
	python -m flask --app backend.run:app seed-db

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

clean:
	rm -rf frontend/dist dist __pycache__ .pytest_cache *.egg-info
