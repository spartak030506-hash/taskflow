#!/bin/bash

set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.5
done
echo "PostgreSQL port is open"
sleep 1
echo "PostgreSQL is ready"

echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.5
done
echo "Redis port is open"
sleep 1
echo "Redis is ready"

exec "$@"
