FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY . /app
RUN python -m pip install '.[api,openai]'

RUN useradd --create-home --uid 10001 gateway
USER gateway

EXPOSE 8000
CMD ["uvicorn", "ai_gateway.api:app", "--host", "0.0.0.0", "--port", "8000"]
