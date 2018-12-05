FROM python:3-alpine
RUN pip install --no-cache-dir pip==18.0
RUN apk add --update git gcc libc-dev libxslt-dev
RUN pip install --no-cache-dir pipenv
COPY src/Pipfile /data/Pipfile
WORKDIR /data/
RUN pipenv --three install
COPY src/ /data/
WORKDIR /data/
ENTRYPOINT [ "pipenv", "run" ]
CMD [ "python", "main.py" ]
