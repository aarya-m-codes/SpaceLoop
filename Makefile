.PHONY: help install dev test test-backend test-frontend build clean docker-up docker-down lint seed

help:
	@echo "SpaceLoop Development & Operational Commands:"
	@echo "  make install         Install backend and frontend dependencies"
	@echo "  make dev             Start backend and frontend development servers"
	@echo "  make test            Run all backend test suites"
	@echo "  make test-backend    Run Python unittest discovery"
	@echo "  make test-frontend   Run frontend tests"
	@echo "  make build           Build production frontend assets"
	@echo "  make lint            Run linters across codebase"
	@echo "  make seed            Seed database with mock listings and users"
	@echo "  make docker-up       Start multi-service Docker containers"
	@echo "  make docker-down     Stop Docker containers"
	@echo "  make clean           Remove cached files and build artifacts"

install:
	pip install -r requirements.txt
	npm install

dev:
	@echo "Starting development environment..."
	npm run dev & python app.py

test: test-backend

test-backend:
	python -m unittest discover -s tests -p "test_*.py"

test-frontend:
	npm run build

build:
	npm run build

lint:
	npx prettier --check "src/**/*.{js,jsx,css}" || true
	python -m pyflakes backend/ app.py models.py security.py || true

seed:
	python seed_data.py

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

clean:
	rm -rf dist __pycache__ .pytest_cache *.egg-info
	find . -type d -name "__pycache__" -exec rm -r {} +
