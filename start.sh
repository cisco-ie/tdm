#!/usr/bin/env bash
function check_sysctl() {
    ES_VM_MAX_MAP_COUNT_MIN=262144
    ES_VM_MAX_MAP_COUNT=$(sysctl -n vm.max_map_count)
    if [ "$ES_VM_MAX_MAP_COUNT" -lt "$ES_VM_MAX_MAP_COUNT_MIN" ]; then
        echo "vm.max_map_count=$ES_VM_MAX_MAP_COUNT is below ElasticSearch's recommended $ES_VM_MAX_MAP_COUNT_MIN."
        echo "Recommend running \"sysctl -w vm.max_map_count=$ES_VM_MAX_MAP_COUNT_MIN\""
        echo "The system will still function, but against recommended settings."
        read -p "Press [Enter] to continue."
    fi
}

UNAME="$(uname -s)"
case "${UNAME}" in
    Linux*)
        check_sysctl
        ;;
    *)
        echo "Recommend running on Linux for production purposes."
        echo "YMMV on Windows or MacOS."
        sleep 5s
        ;;
esac
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
        ;;
esac
docker-compose -f $COMPOSE_FILE up -d --build
