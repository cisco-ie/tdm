FROM node:alpine
WORKDIR /data/
RUN apk update && apk add ca-certificates && update-ca-certificates
RUN wget https://github.com/remingtonc/vuepress/archive/no-dist-delete.tar.gz
RUN tar --extract --gzip --file no-dist-delete.tar.gz --strip=1 
RUN yarn
COPY docs/ /data/docs
ENTRYPOINT [ "yarn" ]
CMD [ "run", "vuepress", "build", "docs" ]
