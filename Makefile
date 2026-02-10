.PHONY: help start stop rebuild purge logs

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  start      Start the application"
	@echo "  stop       Stop the application"
	@echo "  rebuild    Rebuild containers (applies requirements.txt and migrations)"
	@echo "  purge      Remove database, uploads, docker images, and volumes (CAUTION!)"
	@echo "  logs       View logs"

start:
	docker compose up -d

stop:
	docker compose down

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

purge:
	@read -p "Are you sure you want to purge everything (database, uploads, volumes)? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose down -v --rmi all --remove-orphans; \
		rm -rf uploads/*; \
		echo "Purge complete."; \
	else \
		echo "Purge cancelled."; \
	fi

logs:
	docker compose logs -f
