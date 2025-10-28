#!/bin/sh
set -e

echo "Waiting for MySQL at $DB_HOST..."

until mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" &> /dev/null; do
  echo "MySQL is unavailable - sleeping 2s..."
  sleep 2
done

echo "MySQL is up - running tests"
exec "$@"
