# Makefile for Sys Rev Tech Project
# Government Procurement Project Review and Analysis System

.PHONY: help install install-dev setup-pre-commit lint format type-check security-check test test-cov clean run-dev run-prod docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install          - Install production dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo "  setup-pre-commit - Setup pre-commit hooks"
	@echo "  lint             - Run all linting checks"
	@echo "  format           - Format code with black and isort"
	@echo "  type-check       - Run type checking with mypy"
	@echo "  security-check   - Run security checks with bandit"
	@echo "  test             - Run tests"
	@echo "  test-cov         - Run tests with coverage"
	@echo "  clean            - Clean up generated files"
	@echo "  run-dev          - Run development server"
	@echo "  run-prod         - Run production server"
	@echo "  docker-build     - Build Docker images"
	@echo "  docker-up        - Start Docker services"
	@echo "  docker-down      - Stop Docker services"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pre-commit

# Pre-commit setup
setup-pre-commit:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Code quality checks
lint: format type-check security-check
	@echo "All linting checks completed!"

format:
	@echo "Formatting code with black..."
	black app/ tests/ --line-length 88
	@echo "Sorting imports with isort..."
	isort app/ tests/ --profile black
	@echo "Code formatting completed!"

type-check:
	@echo "Running type checks with mypy..."
	mypy app/ --ignore-missing-imports --no-strict-optional
	@echo "Type checking completed!"

security-check:
	@echo "Running security checks with bandit..."
	bandit -r app/ -x tests/ -f json -o bandit-report.json || true
	bandit -r app/ -x tests/
	@echo "Security check completed!"

# Alternative linting with ruff (faster)
lint-ruff:
	@echo "Running ruff checks..."
	ruff check app/ tests/
	ruff format app/ tests/
	@echo "Ruff checks completed!"

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-unit:
	@echo "Running unit tests..."
	pytest tests/ -v -m "unit"

test-integration:
	@echo "Running integration tests..."
	pytest tests/ -v -m "integration"

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -f bandit-report.json
	@echo "Cleanup completed!"

# Development server
run-dev:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
run-prod:
	@echo "Starting production server..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "Services started. Check status with: docker-compose ps"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Database migrations
db-upgrade:
	@echo "Running database migrations..."
	alembic upgrade head

db-downgrade:
	@echo "Reverting database migrations..."
	alembic downgrade -1

db-revision:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Monitoring and logs
monitor:
	@echo "Opening monitoring dashboard..."
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

logs:
	@echo "Showing application logs..."
	tail -f logs/app.log

# Code analysis
analyze:
	@echo "Running code analysis..."
	@echo "Lines of code:"
	find app/ -name "*.py" | xargs wc -l | tail -1
	@echo "\nComplexity analysis:"
	radon cc app/ -a
	@echo "\nMaintainability index:"
	radon mi app/

# Full quality check (CI/CD pipeline)
ci: clean install-dev lint test-cov
	@echo "CI pipeline completed successfully!"

# Quick development setup
setup: install-dev setup-pre-commit
	@echo "Development environment setup completed!"
	@echo "Run 'make run-dev' to start the development server"