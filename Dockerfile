# Fly.io Django + Gunicorn + WhiteNoise
FROM python:3.12-slim

# Avoid interactive prompts during apt installs
ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps 단계 제거 (psycopg[binary] 사용으로 컴파일 불필요)

# Install deps first with caching
COPY requirements.txt /app/requirements.txt

# Install
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Collectstatic은 런타임 entrypoint에서 수행

# Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3", "--timeout", "120"]

EXPOSE 8080
