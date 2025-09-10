## Genz — AI Compose Extension

A privacy-first browser extension that detects text inputs on any webpage, and generates context-aware replies using selectable LLMs (OpenAI, Gemini, Anthropic). Backed by a Next.js web app and a FastAPI backend.

### Monorepo Structure

- `apps/api`: FastAPI service (auth, keys, generation proxy, billing)
- `apps/web`: Next.js app (marketing, dashboard, settings, billing)
- `apps/extension`: Browser extension (content script, background, popup/options)
- `packages/shared`: Shared libraries/types/config
- `infra`: Deployment and ops (CI/CD, helm charts, k8s manifests)

### High-level Architecture

- Browser extension detects inputs, injects UI, collects optional context, and calls either local provider (user key) or server proxy.
- Next.js app provides account, API key management, pricing, and admin.
- FastAPI backend handles auth, rate limits, adapters to providers, metrics, and billing.

### Goals (MVP)

- Detect inputs and inject Compose button
- Single-shot generation with model + tone presets
- Basic auth, API key connect, tiered billing
- Privacy-first defaults with local-key option

### Getting Started

- `apps/api`: FastAPI service with `/api/v1/*` endpoints
- `apps/web`: Next.js app for UI and dashboard
- `apps/extension`: Manifest v3 extension with content/background scripts

Setup instructions will be added in subsequent steps as we scaffold each app.

### License

IntellWe - FardinHash, RianaAzad. All rights reserved.
