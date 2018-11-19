FROM node:alpine
RUN yarn global add vuepress@next
COPY . /data/
ENTRYPOINT [ "vuepress" ]
CMD [ "dev" ]
