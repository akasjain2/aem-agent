# Use official Python image with CUDA/CPU support depending on your host
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install early (layer cache)
COPY requirements.txt .

# Avoid interactive prompts, and install dependencies
RUN apt-get update && apt-get install -y git \
 && pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
