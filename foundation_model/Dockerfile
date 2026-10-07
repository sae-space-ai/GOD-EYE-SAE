# GOD EYE SAE Foundation Model - CPU Validation Dockerfile
# For testing and validation without GPU

FROM python:3.11-slim

LABEL maintainer="GOD EYE SAE Team"
LABEL description="CPU validation environment for LiDAR-SAR foundation model"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY foundation_model/requirements.txt .

# Install Python dependencies (CPU-only PyTorch)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    -f https://download.pytorch.org/whl/cpu/torch_stable.html && \
    pip install --no-cache-dir -r requirements.txt

# Copy foundation model code
COPY foundation_model/ ./foundation_model/

# Set working directory to foundation_model
WORKDIR /app/foundation_model

# Create runtime directories
RUN mkdir -p runtime/checkpoints runtime/logs runtime/outputs runtime/data

# Default command: run environment check
CMD ["python", "check_environment.py"]
