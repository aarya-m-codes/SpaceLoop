.PHONY: all setup dev test build clean docker-up docker-down lint format

all: setup

setup:
	@echo "Installing frontend dependencies..."
	npm install
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt

dev:
	@echo "Starting full development stack..."
	npm run dev

test:
	@echo "Running tests..."
	npm test --if-present
	pytest tests/

build:
	@echo "Building frontend..."
	npm run build

lint:
	@echo "Linting source..."
	npx eslint src/ --ext .js,.jsx || true
	flake8 backend/ --max-line-length=120 || true

format:
	@echo "Formatting code..."
	npx prettier --write "src/**/*.{js,jsx,css}" || true

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf dist build .pytest_cache htmlcov
