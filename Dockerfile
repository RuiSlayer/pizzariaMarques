# Python 3.9 is what the project is developed against (Django 3.2 does not support 3.11+).
FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --uid 1000 --no-create-home app

COPY manage.py docker-entrypoint.sh ./
COPY PizzariaMarques PizzariaMarques
COPY sitepizza sitepizza
# The product photos are copied into the storage volume on first start (docker-entrypoint.sh),
# because the volume mounted at /app/storage would otherwise hide them.
COPY storage/produtos storage-seed/produtos

# Hashed + compressed static files for WhiteNoise. The key is only needed to load the settings.
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && mkdir storage \
    && chown app:app storage

USER app
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "PizzariaMarques.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
