FROM python:3.14-slim

WORKDIR /app

# Install build dependencies and clean apt list to keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set a default DB URL for local development; Compose can override it.
ENV DATABASE_URL=postgresql://postgres:postgres@postgres:5432/voting_db

# Create upload directory and ensure permissions
RUN mkdir -p /app/static/uploads

EXPOSE 8000
CMD ["uvicorn main:app --host 0.0.0.0 --port 8000"]
