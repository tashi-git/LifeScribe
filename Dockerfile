# Use a lightweight Python image based on Debian
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and use unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for MySQL client
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire application (app + tests)
COPY . .

# Environment variables for MySQL connection
ENV DB_HOST=mysql
ENV DB_USER=testuser
ENV DB_PASSWORD=testpass
ENV DB_NAME=test_diary_app

# Default command to run tests
CMD ["pytest", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"]
