FROM node:alpine
WORKDIR /data/
# Fix proxy issues
RUN apk update && apk --no-cache add openssl wget
RUN wget https://github.com/vuejs/vuepress/archive/master.tar.gz
RUN tar --extract --gzip --file master.tar.gz --strip=1 && rm master.tar.gz
RUN yarn
COPY docs/ /data/docs
ENTRYPOINT [ "yarn" ]
CMD [ "run", "vuepress", "build", "docs" ]
