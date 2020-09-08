FROM python:3.7-slim

MAINTAINER Jean Pommier "jean.pommier@pi-geosolutions.fr"

COPY docker/resources /
COPY requirements.txt /requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3-dev && \
    pip install uwsgi && pip install -r /requirements.txt && \
    apt-get remove -y build-essential python-dev && \
    rm -rf /var/lib/apt/lists/*

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN mkdir /data && \
    groupadd --gid 999 www && \
    useradd -r -ms /bin/bash --uid 999 --gid 999 www && \
    chown www:www /data

EXPOSE 5000

RUN chmod +x /docker-entrypoint.sh /docker-entrypoint.d/*

COPY --chown=www:www app /app

WORKDIR "/app"

VOLUME ["/data"]

USER www

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--http", ":5000", "--chdir", "/app", "--wsgi-file", "main.py", "--callable", "app", "--master", "--processes", "4", "--threads", "2", "--uid", "www", "--stats", "127.0.0.1:9191"]
