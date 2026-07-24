.PHONY: help build dev prod up down logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build
	docker-compose -f docker-compose.prod.yml build

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development environment started at http://localhost:8000"

prod: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production environment started at http://localhost:8000"

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

down-prod: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show logs from API service
	docker-compose logs -f api

clean: ## Stop and remove all containers, volumes, and images
	docker-compose down -v
	docker system prune -af

# Testing targets
test: ## Run all tests
	docker-compose run --rm api python -m pytest tests/ -v

test-unit: ## Run unit tests only
	docker-compose run --rm api python -m pytest tests/ -v -m unit

test-integration: ## Run integration tests only
	docker-compose run --rm api python -m pytest tests/ -v -m integration

test-e2e: ## Run end-to-end tests only
	docker-compose run --rm api python -m pytest tests/ -v -m e2e

test-smoke: ## Run smoke tests (critical functionality)
	docker-compose run --rm api python -m pytest tests/ -v -m smoke

test-coverage: ## Run tests with coverage report
	docker-compose run --rm api python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-fast: ## Run fast tests (skip slow tests)
	docker-compose run --rm api python -m pytest tests/ -v -m "not slow"

# Code quality targets
lint: ## Run linter in Docker
	docker-compose run --rm api python -m flake8 src/ tests/

format: ## Format code with black and isort
	docker-compose run --rm api python -m black src/ tests/
	docker-compose run --rm api python -m isort src/ tests/

check-format: ## Check if code is formatted
	docker-compose run --rm api python -m black --check src/ tests/
	docker-compose run --rm api python -m isort --check-only src/ tests/

type-check: ## Run type checking with mypy
	docker-compose run --rm api python -m mypy src/

# Local development targets (without Docker)
test-local: ## Run tests locally (requires venv)
	source venv/bin/activate && python -m pytest tests/ -v

test-coverage-local: ## Run tests with coverage locally
	source venv/bin/activate && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint-local: ## Run linter locally
	source venv/bin/activate && python -m flake8 src/ tests/

format-local: ## Format code locally
	source venv/bin/activate && python -m black src/ tests/
	source venv/bin/activate && python -m isort src/ tests/

# Utility targets
shell: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-prod: ## Open shell in production API container
	docker-compose -f docker-compose.prod.yml exec api /bin/bash

health: ## Check health of all services
	@curl -f http://localhost:8000/health || echo "API not healthy"

db-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

rebuild: ## Rebuild and restart services
	docker-compose up -d --build

rebuild-prod: ## Rebuild and restart production services
	docker-compose -f docker-compose.prod.yml up -d --build

monitoring: ## Start monitoring stack
	docker-compose --profile monitoring up -d
	@echo "Monitoring stack started: Prometheus at http://localhost:9090, Grafana at http://localhost:3000"

install-deps: ## Install dependencies locally
	python3 -m venv venv
	source venv/bin/activate && pip install --upgrade pip
	source venv/bin/activate && pip install -r requirements.txt
	source venv/bin/activate && pip install -r requirements-dev.txt

ci: ## Run full CI pipeline (test, lint, type-check)
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) lint
	$(MAKE) type-check
	@echo "CI pipeline completed successfully"