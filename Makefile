GIT_VERSION := $(shell git describe --abbrev=8 --always --tags)
DATE := $(shell date +%Y%m%d)

all: docker-build-latest

fresh: docker-pull-deps docker-build-latest

fresh-push: docker-pull-deps docker-build-push

docker-pull-deps:
	docker pull python:3.7

docker-build-latest:
	docker build -t pigeosolutions/bn-backend:latest .

docker-build-push: docker-build-latest
	docker tag pigeosolutions/bn-backend:latest pigeosolutions/bn-backend:${DATE}-${GIT_VERSION}
	docker push pigeosolutions/bn-backend:latest
	docker push pigeosolutions/bn-backend:${DATE}-${GIT_VERSION}
