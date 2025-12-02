.PHONY: help install dev up down logs clean test format lint proto check

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies with Poetry"
	@echo "  make dev        - Run development environment"
	@echo "  make up         - Start all services with docker-compose"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - Show logs from all services"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run tests"
	@echo "  make check      - Check if all services are running"
	@echo "  make format     - Format code with black"
	@echo "  make lint       - Lint code with ruff"
	@echo "  make proto      - Generate gRPC code from proto files"

install:
	poetry install

dev:
	docker-compose up --build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	poetry run pytest -v

check:
	@./scripts/test_setup.sh

format:
	poetry run black backend ml
	cd frontend && npm run format

lint:
	poetry run ruff check backend ml
	poetry run mypy backend ml

proto:
	python -m grpc_tools.protoc \
		-I./protos \
		--python_out=./backend/services \
		--grpc_python_out=./backend/services \
		./protos/*.proto
