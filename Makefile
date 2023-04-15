.PHONY: help
help:
	cat Makefile

.PHONY: build
build:
	docker build -t discord_crawler .

.PHONY: dev-migrate
dev-migrate:


.PHONY: prod-migrate
prod-migrate:

.PHONY: pg_cron
pg_cron:
	docker container exec \
		-it postgres \
		psql postgres://postgres@localhost/discord_data_dev -c 'refresh materialized view mv_channel_stats;'
