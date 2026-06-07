# Stage 1: Build compilation dependencies
FROM python:3.11-slim AS compiler

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a local user path
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Build final lightweight container
FROM python:3.11-slim AS production

WORKDIR /app

# Copy python packages from the build stage
COPY --from=compiler /root/.local /root/.local
COPY . .

# Configure path variables and environment settings
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV TEMP_SPOOL_DIR=/tmp/spooled_files

EXPOSE 8000

# Run Uvicorn utilizing a production ASGI configuration on app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
