# ==================================================
# DEVELOPMENT COMMANDS
# ==================================================

start:
    docker compose up -d

run:
    python manage.py runserver

worker:
    watchmedo auto-restart --recursive --pattern='*.py' -- celery -A config worker -l INFO

infra:
    docker compose up -d database cache broker mailing

prod:
    docker compose up -d api

bueno:
    uvicorn tests.providers.bueno:app --reload --port 8002

uklon:
    uvicorn tests.providers.uklon:app --reload --port 8003

uber:
    uvicorn tests.providers.uber:app --reload --port 8004

# ==================================================
# CODE QUALITY
# ==================================================

check:
    black --check ./
    isort --check ./
    flake8 ./
    mypy ./

quality:
    black ./
    isort ./