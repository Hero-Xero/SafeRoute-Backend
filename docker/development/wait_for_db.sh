#!/bin/sh

# wait-for-db.sh
set -e

host="saferoute-db"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL at $host:5432..."
  sleep 1
done

echo "PostgreSQL is up, executing command."
