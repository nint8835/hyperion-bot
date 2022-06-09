FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip install poetry && \
    poetry install --no-root --no-dev

CMD ["python", "bot.py"]