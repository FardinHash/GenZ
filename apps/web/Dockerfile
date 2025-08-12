# syntax=docker/dockerfile:1
FROM node:20-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* apps/web/pnpm-lock.yaml* ./
RUN npm ci || npm install

FROM node:20-alpine AS build
WORKDIR /app
COPY apps/web .
RUN mkdir -p public
RUN npm ci || npm install
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000
COPY --from=build /app/.next /app/.next
COPY --from=build /app/public /app/public
COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/package.json /app/package.json

EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"] 