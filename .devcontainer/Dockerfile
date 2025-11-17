FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement files into dev environment
COPY ../requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Default shell
SHELL ["/bin/bash", "-c"]
