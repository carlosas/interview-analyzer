.PHONY: help install start stop restart logs purge rebuild poetry-lock-update shell migrate tests lint

COMPOSE = COMPOSE_BAKE=true docker compose

help:
	@echo "Available commands:"
	@echo "  make install              - Build images and run migrations"
	@echo "  make start                - Start all services in detached mode"
	@echo "  make stop                 - Stop all services"
	@echo "  make restart              - Restart all services"
	@echo "  make migrate              - Run migrations"
	@echo "  make tests                - Run test suite"
	@echo "  make lint                 - Run ruff linting and formatting checks"
	@echo "  make logs                 - Show logs from all services"
	@echo "  make purge                - Remove all containers, images, networks and volumes"
	@echo "  make rebuild              - Rebuild images without cache and restart"
	@echo "  make poetry-lock-update   - Update lock files (upgrades to latest compatible)"
	@echo "  make shell                - Open bash shell in app container"

install:
	@echo "Building Docker images..."
	$(COMPOSE) build
	@echo "Running migrations..."
	$(COMPOSE) run --rm app python manage.py migrate
	$(COMPOSE) stop db redis
	@echo "Installation complete!"

start:
	@echo "Starting services..."
	$(COMPOSE) up -d
	@echo "Services started!"
	@echo "App: http://localhost:8501"
	@echo "Adminer: http://localhost:8080"

stop:
	@echo "Stopping services..."
	$(COMPOSE) stop
	@echo "Services stopped!"

restart: stop start

logs:
	$(COMPOSE) logs -f

purge:
	@echo "WARNING: This will remove all containers, images, networks and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Stopping and removing containers..."; \
		$(COMPOSE) down -v --remove-orphans; \
		echo "Removing images..."; \
		$(COMPOSE) down --rmi all -v --remove-orphans; \
		echo "Removing dangling volumes..."; \
		docker volume prune -f; \
		echo "Purge complete!"; \
	else \
		echo "Purge cancelled."; \
	fi

rebuild:
	@echo "Rebuilding images without cache..."
	$(COMPOSE) build --no-cache
	@echo "Restarting services..."
	$(COMPOSE) up -d --force-recreate
	@echo "Running migrations..."
	$(COMPOSE) run --rm app python manage.py migrate
	@echo "Rebuild complete!"

poetry-lock-update:
	@echo "Generating Poetry lock files..."
	$(COMPOSE) run --rm app poetry lock
	@echo "Rebuilding with lock files..."
	$(COMPOSE) build
	@echo "Update complete!"

shell:
	$(COMPOSE) exec app bash

migrate:
	@echo "Running migrations..."
	$(COMPOSE) run --rm app python manage.py migrate

lint:
	@echo "Running ruff checks and formatting..."
	$(COMPOSE) run --rm app ruff check --fix --exit-zero .
	$(COMPOSE) run --rm app ruff format .
	@echo "Lint checks complete!"

tests:
	@echo "Running tests..."
	$(COMPOSE) run --rm app python manage.py test tests
	@echo "Tests complete!"
