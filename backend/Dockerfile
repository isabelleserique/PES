FROM node:20-bookworm-slim AS node

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules

RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r backend/requirements.txt

COPY backend/package.json backend/package-lock.json backend/
RUN cd backend && npm ci

COPY backend backend
RUN cd backend && npx prisma generate --schema prisma/schema.prisma

EXPOSE 8000

CMD ["sh", "backend/scripts/start_render.sh"]
