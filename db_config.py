import os

db_config = {
    'host': os.getenv('DB_HOST', 'host.docker.internal'),
    'user': os.getenv('DB_USER', 'root'),          # your MySQL username
    'password': os.getenv('DB_PASSWORD', 'root@12345'),
    'database': os.getenv('DB_NAME', 'diary_db')
}
