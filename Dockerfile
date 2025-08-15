FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_DIR="/app"

WORKDIR $APP_DIR

COPY requirements.txt $APP_DIR/

RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install -r requirements.txt

COPY . $APP_DIR/

CMD ["python", "main.py"]