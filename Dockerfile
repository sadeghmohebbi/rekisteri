FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for building Python packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files and install packages into a virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port Gunicorn will listen on (default 8000)
EXPOSE 5000

# Run with Gunicorn (adjust module:app to your entry point)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
