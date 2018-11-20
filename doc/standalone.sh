#!/usr/bin/env bash
docker build -t tdm/doc_test .
docker run -d -p 8089:8080 -v $(pwd)/docs:/data/docs:rw --name tdm_dev_docs tdm/doc_test run vuepress dev docs
