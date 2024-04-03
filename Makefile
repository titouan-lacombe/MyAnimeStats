COMPOSE=docker compose -p myanimestats

default: up

mkdata:
	@mkdir -p data

up: mkdata
	@$(COMPOSE) up -d

recreate: mkdata
	@$(COMPOSE) up -d --force-recreate

down:
	@$(COMPOSE) down --remove-orphans

logs:
	@$(COMPOSE) logs -f

attach:
	@$(COMPOSE) exec $(app) bash

notebook:
	@pdm run jupyter notebook myanimestats.ipynb
