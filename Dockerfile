# Dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 gdpbzn && chown -R gdpbzn:gdpbzn /app
USER gdpbzn

# Create uploads directory
RUN mkdir -p app/static/uploads

# Run the application
CMD ["python", "run.py"]