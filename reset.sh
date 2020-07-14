#!/usr/bin/env bash
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
docker-compose -f $COMPOSE_FILE down --rmi all --volumes
sudo rm -rf ../etl/cache/transform/*
sudo rm -rf ../etl/cache/extract/*
