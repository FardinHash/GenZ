## Infrastructure

This directory will contain deploy and ops assets. For development observability we added:

- Sentry (API) via `SENTRY_DSN`
- Prometheus metrics at `/metrics`

### Docker (local dev)

- API `apps/api` Dockerfile (to add):
  - Base: python:3.12-slim, install deps, copy app, expose 8000
- Web `apps/web` Dockerfile (to add):
  - Base: node:20, install, build, run on 3000
- Extension is built via Vite and published to `dist/`

Docker Compose (to create):

- api: build `apps/api`, env from `.env`, ports `8000:8000`
- web: build `apps/web`, env NEXT_PUBLIC_API_BASE_URL, ports `3000:3000`
- db: postgres:16, volume, env POSTGRES_PASSWORD
- redis: redis:7
- prometheus: official image, scrape api `/metrics`
- grafana: provision dashboard (optional)

### Sentry (test/dev)

- Create a Sentry project (Python/JS), get DSNs
- Set `SENTRY_DSN` in `apps/api/.env`
- For web, add Sentry SDK (next step) and DSN in `.env.local`

### Prometheus/Grafana

- Prometheus scrape config:

```
scrape_configs:
  - job_name: genz_api
    static_configs:
      - targets: ['api:8000']
```

- Grafana: add Prometheus datasource and import a FastAPI/Prometheus dashboard

### Kubernetes (next)

- Helm charts per service:
  - Deployment + Service for api, web
  - Secrets via Kubernetes Secrets or external Vault
  - Ingress (Nginx/Traefik)
  - ConfigMaps for app config
- Add ServiceMonitor (Prometheus Operator) for `/metrics`
- Sentry DSN via Secret

### CI/CD (next)

- GitHub Actions:
  - Lint/test → build Docker images → push to registry
  - Deploy to staging cluster using Helm
  - Run smoke tests

### Secrets

- Use `.env` in dev; in staging/prod store in cloud secret manager or Vault
- Stripe keys, JWT secrets, Sentry DSN, DB creds
