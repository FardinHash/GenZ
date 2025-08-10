## FastAPI Service

Implements auth, user, API keys, generation proxy, billing, and admin endpoints.

### Essential Endpoints

- POST `/api/v1/auth/signup`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- GET `/api/v1/user/me`
- PUT `/api/v1/user/me/settings`
- POST `/api/v1/keys`
- GET `/api/v1/keys`
- DELETE `/api/v1/keys/{id}`
- POST `/api/v1/generate`
- GET `/api/v1/generate/{id}/status`
- POST `/api/v1/billing/subscribe`
- POST `/api/v1/billing/webhook`
- GET `/api/v1/admin/usage`
- GET `/api/v1/admin/requests`

Skeleton code will be added in the next step.
