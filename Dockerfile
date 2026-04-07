FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for lxml
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create book folders in root
RUN mkdir -p /books/pending /books/transfered

CMD ["python", "src/bot.py"]
