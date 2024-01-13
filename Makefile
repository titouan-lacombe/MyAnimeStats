COMPOSE=docker compose -p myanimestats

include .env
export

default: up

up:
	${COMPOSE} up -d

recreate:
	${COMPOSE} up -d --force-recreate

down:
	${COMPOSE} down --remove-orphans

logs:
	${COMPOSE} logs -f
