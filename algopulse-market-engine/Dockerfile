FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY README.md HANDOFF_TO_CLAUDE.md ./

ENV PYTHONPATH=/app/src
ENV ALGO_PULSE_DATA_DIR=/app/data
ENV ALGO_PULSE_DATABASE=/app/data/market.db

EXPOSE 8765

CMD ["uvicorn", "algopulse.api:app", "--host", "0.0.0.0", "--port", "8765"]
