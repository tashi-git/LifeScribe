# Use a lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire application
COPY . .

# Make wait script executable
RUN chmod +x wait-for-mysql.sh

# Environment variables (defaults, can be overridden)
ENV DB_HOST=mysql \
    DB_USER=testuser \
    DB_PASSWORD=testpass \
    DB_NAME=test_diary_app

# Default test command
CMD ["./wait-for-mysql.sh", "pytest", "test_app.py", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"]
