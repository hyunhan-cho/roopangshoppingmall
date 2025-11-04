# Fly.io Django + Gunicorn + WhiteNoise
FROM python:3.12-slim

# Avoid interactive prompts during apt installs
ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps 단계 제거 (psycopg[binary] 사용으로 컴파일 불필요)

# Copy project
COPY . /app

# Install
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn whitenoise psycopg[binary]

# Collect static at build time (optional)
RUN python manage.py collectstatic --noinput || true

# Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3", "--timeout", "120"]

EXPOSE 8080
