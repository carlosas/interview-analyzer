COMPOSE := COMPOSE_BAKE=true docker compose

.PHONY: help start stop rebuild purge logs lint

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  start      Start the application"
	@echo "  stop       Stop the application"
	@echo "  rebuild    Rebuild containers (applies requirements.txt and migrations)"
	@echo "  purge      Remove database, uploads, docker images, and volumes (CAUTION!)"
	@echo "  logs       View logs"
	@echo "  integrate  Run autopep8 linter on src directory"

start:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

rebuild:
	$(COMPOSE) down
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

purge:
	@read -p "Are you sure you want to purge everything (database, uploads, volumes)? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(COMPOSE) down -v --rmi all --remove-orphans; \
		rm -rf uploads/*; \
		echo "Purge complete."; \
	else \
		echo "Purge cancelled."; \
	fi

logs:
	$(COMPOSE) logs -f

integrate:
	$(COMPOSE) exec streamlit-app autopep8 --in-place --recursive src
