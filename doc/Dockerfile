FROM node:alpine
WORKDIR /data/
RUN yarn global add vuepress@next
COPY package.json package.json
COPY docs/ docs/
ENTRYPOINT [ "yarn" ]
CMD [ "docs:build" ]
