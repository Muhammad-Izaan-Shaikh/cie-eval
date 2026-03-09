FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/papers uploads/markschemes uploads/images

EXPOSE 8000

# --timeout-keep-alive 120: keeps connections open for slow uploads
# --limit-max-requests 0: no artificial request limit
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--timeout-keep-alive", "120", "--limit-concurrency", "50"]
