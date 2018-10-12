#!/usr/bin/env bash
./stop.sh $1
if [ $? -ne 0 ]; then
    echo "Stop encountered errors! Not deleting volumes."
    exit 1
fi
echo "Sleeping 5 seconds before deleting volumes."
sleep 5
docker volume rm tdm_dbms_storage tdm_nginx_logs tdm_goaccess_report tdm_search_storage
