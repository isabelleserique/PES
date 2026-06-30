#!/bin/sh
set -eu

cd /app/backend
npx prisma generate --schema prisma/schema.prisma
npx prisma migrate deploy --schema prisma/schema.prisma

cd /app
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
