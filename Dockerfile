FROM python:3.5

MAINTAINER Jean Pommier "jean.pommier@pi-geosolutions.fr"

RUN apt-get update && \
    apt-get install -y \
        python3 \
    && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uwsgi

COPY docker/resources /
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8


RUN mkdir /data && \
    groupadd --gid 999 www && \
    useradd -r -ms /bin/bash --uid 999 --gid 999 www && \
    chown www:www /data

EXPOSE 5000

RUN chmod +x /docker-entrypoint.sh /docker-entrypoint.d/*

COPY --chown=www:www app /app
COPY --chown=www:www app/stations-experimental /data/stations-experimental

WORKDIR "/app"

VOLUME ["/data"]

USER www

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--http", ":5000", "--chdir", "/app", "--wsgi-file", "main.py", "--callable", "app", "--master", "--processes", "4", "--threads", "2", "--uid", "www", "--stats", "127.0.0.1:9191"]
