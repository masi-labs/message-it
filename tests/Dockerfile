# syntax=docker/dockerfile:1.4

FROM python:3.14-alpine

ENV PYTHONPATH=/code
ENV PYTHONOPTIMIZE=''
ENV PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache git openssh-client

RUN mkdir -p /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts

COPY requirements/* /code/requirements/

RUN --mount=type=ssh pip install -r /code/requirements/dev.txt

WORKDIR /code
