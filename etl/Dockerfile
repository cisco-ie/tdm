FROM python:3-alpine
RUN pip install --no-cache-dir pip==18.0
RUN apk add --update git gcc libc-dev libxslt-dev
RUN pip install --no-cache-dir pipenv
WORKDIR /data/
COPY src/Pipfile Pipfile
RUN pipenv --three install
COPY src/ .
ENTRYPOINT [ "pipenv", "run" ]
CMD [ "python", "main.py" ]
