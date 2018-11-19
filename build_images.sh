#!/usr/bin/env bash
docker build -t tdm/etl etl/
docker build -t tdm/web web/
docker build -t tdm/doc doc/
