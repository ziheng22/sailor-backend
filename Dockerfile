FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seed.py sync_slugs.py ./

RUN mkdir -p /data/uploads && chown -R appuser:appuser /data /app

ENV APP_ENV=production \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8000 \
    DATABASE_URL=sqlite:////data/sailor.db \
    UPLOAD_DIR=/data/uploads

EXPOSE 8000

USER appuser

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "2", "--access-logfile", "-", "--error-logfile", "-"]
