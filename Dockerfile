FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DB_HOST=host.docker.internal
ENV DB_USER=root
ENV DB_PASSWORD=root@12345
ENV DB_NAME=diary_db

EXPOSE 5000

CMD ["python", "app.py"]
