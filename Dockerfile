FROM python:3.12-slim

# ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    # dependencies for building Python packages && cleaning apt apt packages
    && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --upgrade pip setuptools pipenv


# aka ``cd``
WORKDIR /app/

# aka ``cp`` on unix
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

# copy the project
COPY config ./

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]