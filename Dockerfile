FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Install OS dependencies (in a single layer, with cleanup)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-por \
    poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set PYTHONPATH for proper module resolution
ENV PYTHONPATH=/app/src

# Copy only requirements file and install dependencies first to leverage caching
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src ./src
COPY .env .

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
