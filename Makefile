COMPOSE=docker compose -p myanimestats

include .env
export

default: up

build:
	@envsubst < jikan.env.tpl > jikan.env

up: build
	@$(COMPOSE) up -d

recreate: build
	@$(COMPOSE) up -d --force-recreate

down:
	@$(COMPOSE) down --remove-orphans

logs:
	@$(COMPOSE) logs -f

attach:
	@$(COMPOSE) exec $(app) bash

notebook:
	@pipenv run jupyter notebook myanimestats.ipynb
