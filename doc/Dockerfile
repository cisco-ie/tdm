FROM node:alpine
RUN yarn global add vuepress@next
WORKDIR /data/
COPY docs/ /data/
ENTRYPOINT [ "vuepress" ]
CMD [ "build" ]
