FROM node:alpine
WORKDIR /data/
RUN yarn global add vuepress@next
COPY docs/ /data/docs
ENTRYPOINT [ "yarn" ]
CMD [ "run", "vuepress", "build", "docs" ]
