#!/usr/bin/env bash
docker build -t tdm/web web/
COMPOSE_FILE=""
case "$1" in
    ""|"http")
        COMPOSE_FILE=docker-compose.yml
        ;;
    "https")
        COMPOSE_FILE=docker-compose.https.yml
        ;;
    *)
        echo $"Usage: $0 [http|https]"
        exit 1
esac
docker-compose -f $COMPOSE_FILE up -d --no-deps web
