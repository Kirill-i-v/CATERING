FROM python:3.12-slim AS base

# ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip setuptools pipenv watchdog
COPY Pipfile Pipfile.lock ./
WORKDIR /app/

COPY ./ ./


RUN pipenv install --deploy --system

ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:8000"

EXPOSE 8000
ENTRYPOINT ["python"]
CMD ["-m", "gunicorn", "config.wsgi:application"]