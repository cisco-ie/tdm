FROM python:3-alpine
WORKDIR /data/
RUN pip install --no-cache-dir pip==18.0
RUN pip install --no-cache-dir pipenv
COPY src/Pipfile Pipfile
RUN apk add --no-cache --virtual .build-deps gcc file make musl-dev libffi-dev libevent-dev
RUN pipenv --three install
RUN apk del .build-deps gcc musl-dev
COPY src/ .
EXPOSE 80
ENTRYPOINT [ "pipenv", "run" ]
CMD [ "python", "runserver.py" ]
