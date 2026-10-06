# Stage 1: Build dependency wheels
FROM python:3.11-slim AS builder

WORKDIR /install
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \
    && pip install --no-cache-dir --prefix=/install/deps -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Non-root user setup for security
RUN useradd -m -u 1001 devopsuser

COPY --from=builder /install/deps /usr/local
COPY . /app

RUN chown -R devopsuser:devopsuser /app
USER 1001

EXPOSE 5000

ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python", "app/app.py"]