#!/usr/bin/env bash
docker build -t tdm/doc_test .
docker run -d -p 8089:8080 -v docs:/data/docs:rw tdm/doc_test run vuepress dev docs
