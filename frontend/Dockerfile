# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# API URL
ARG API_BASE_URL=https://eversondental.onrender.com
ENV API_BASE_URL=$API_BASE_URL

# Copiar package files
COPY frontend/package*.json ./

# Instalar dependencias
RUN npm install

# Copiar frontend
COPY frontend/ ./

# Copiar módulos frontend
COPY backend/app/modules/ /module_layers/

# Build Nuxt
RUN npm run build


# Production stage
FROM node:20-alpine

WORKDIR /app

# Aplicación compilada
COPY --from=builder /app/.output /app/.output

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]