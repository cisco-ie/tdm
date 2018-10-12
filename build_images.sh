#!/usr/bin/env bash
cd etl
docker build -t tdm/etl .
cd ..
cd web
docker build -t tdm/web .
cd ..
