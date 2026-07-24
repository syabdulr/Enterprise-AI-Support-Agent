.PHONY: help build dev prod up down logs clean test lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

test: ## Run tests in Docker
	docker-compose run --rm api python -m pytest tests/ -v

lint: ## Run linter in Docker
	docker-compose run --rm api python -m flake8 src/ tests/

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