FROM python:3-alpine
RUN pip install --no-cache-dir pip==18.0
RUN pip install --no-cache-dir pipenv
COPY src/Pipfile /data/Pipfile
WORKDIR /data/
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN pipenv --three install
RUN apk del .build-deps gcc musl-dev
COPY src/ /data/
WORKDIR /data/
EXPOSE 80
ENTRYPOINT [ "pipenv", "run" ]
CMD [ "python", "runserver.py" ]
