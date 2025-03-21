COMPOSE=docker compose

PUID=$(shell id -u)
PGID=$(shell id -g)

export

default: up

mkdata:
	@mkdir -p data data

build:
	@$(COMPOSE) build

up: mkdata
	@$(COMPOSE) up -d

rebuild: mkdata
	@$(COMPOSE) up -d --build

recreate: mkdata
	@$(COMPOSE) up -d --force-recreate

down:
	@$(COMPOSE) down  --remove-orphans

restart:
	@$(COMPOSE) restart

ps:
	@$(COMPOSE) ps

stats:
	@$(COMPOSE) stats

logs:
	@$(COMPOSE) logs app -f --tail=100

attach:
	@$(COMPOSE) exec app bash
