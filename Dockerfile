# Use a lightweight Python base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the project
COPY . .

# Ensure the wait script is executable
RUN chmod +x wait-for-mysql.sh

# Default env values (can be overridden)
ENV DB_HOST=mysql
ENV DB_USER=testuser
ENV DB_PASSWORD=testpass
ENV DB_NAME=test_diary_app

# Default test command (can be overridden by docker-compose)
CMD ["./wait-for-mysql.sh", "pytest", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"]
