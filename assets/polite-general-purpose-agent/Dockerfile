FROM python:3.12-slim

# Set uv cache to a writable directory (default /.cache/uv is read-only in the runtime)
ENV UV_CACHE_DIR=/tmp/.cache/uv

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application source
COPY app/ ./

EXPOSE 5000

CMD ["python", "main.py"]
