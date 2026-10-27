# py-commerce

A simple e-commerce system for learning FastAPI and monorepo management.

| Path | What | Tooling |
|---|---|---|
| `apps/api` | FastAPI backend (async SQLAlchemy 2.0, Alembic) | uv workspace member |
| `apps/web` | Next.js frontend | npm workspace member |
| `packages/api-client` | TypeScript client generated from the API's OpenAPI schema | npm workspace member |

[Turborepo](https://turborepo.com) runs tasks across both languages. Each Python app has a small `package.json` whose scripts call `uv run ...`. Postgres runs in Docker Compose, and the apps run on your machine so they hot-reload.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.13 itself)
- Node 24 + npm 11
- Docker (with Compose)

## Setup

```bash
cp .env.example .env
npm run setup        # uv sync && npm install
npm run db:migrate   # starts Postgres if needed, then applies migrations
npm run db:seed      # optional: insert 50 mock products (each run adds 50 more)
npm run db:seed:users  # optional: create a default user and an admin (see Auth)
```

## Daily commands

| Task | Command |
|---|---|
| Run everything (Postgres + API :8000 + web :3000) | `npm run dev` |
| Lint / typecheck / test / build | `npm run lint` · `npm run typecheck` · `npm run test` · `npm run build` |
| Add a Python dependency to the API | `uv add <pkg> --package api` |
| Add a JS dependency to the web app | `npm install <pkg> -w web` |
| Create a migration (autogenerate from models) | `npm run db:revision -w api -- -m "add products"` |
| Apply migrations | `npm run db:migrate` |
| Insert 50 mock products | `npm run db:seed` |
| Create the default user and admin | `npm run db:seed:users` |
| Regenerate the TS client by hand | `npx turbo run generate` |
| Browse the database (pgweb on http://localhost:8081) | `npm run db:view` |

API docs: http://localhost:8000/docs

## Products API

| Method | Path | Notes |
|---|---|---|
| `GET` | `/products?page=1&page_size=10` | Newest first. Returns `{ items, total, page, page_size, pages }` |
| `GET` | `/products/{id}` | 404 if missing or deleted |
| `POST` | `/products` | **Admin only.** Body: `{ name, description, price }`. Returns 201 |
| `PUT` | `/products/{id}` | **Admin only.** Same body as create; replaces the editable fields |
| `DELETE` | `/products/{id}` | **Admin only.** Soft delete: sets `deleted_at`. Returns 204 |

- **Prices are integers in cents** (`1299` = $12.99). The web app takes and shows USD and converts at the edge (`apps/web/src/lib/money.ts`).
- Soft-deleted products stay in the table but are hidden from every endpoint.
- Anyone can read products, even when signed out. Admin-only endpoints return 401 when signed out and 403 for non-admins.

## Auth

Auth uses server-side sessions, not JWTs. Signing in creates a row in the `sessions` table, and its random token goes back in an `HttpOnly`, `SameSite=lax` cookie named `session_id`. Every request looks that token up. Signing out deletes the row, so the session ends right away. Sessions expire after `SESSION_TTL_DAYS` (default 7). Passwords are hashed with argon2 ([pwdlib](https://github.com/frankie567/pwdlib)).

| Method | Path | Notes |
|---|---|---|
| `POST` | `/auth/signup` | Body: `{ name, email, password }` (password 8–128 chars). Creates a `user` and signs in. 409 if the email is taken |
| `POST` | `/auth/login` | Body: `{ email, password }`. Sets the cookie. 401 on bad credentials |
| `POST` | `/auth/logout` | Deletes the session and clears the cookie. Returns 204 |
| `GET` | `/auth/me` | The signed-in user, or 401 |

- **Roles:** `user` (the default) and `admin`. Signup always creates a `user`. To make someone an admin, change it in the database:
  ```bash
  docker compose exec postgres psql -U postgres -d pycommerce \
    -c "UPDATE users SET role = 'admin' WHERE email = 'someone@example.com';"
  ```
- **Seed accounts** (`npm run db:seed:users`, safe to re-run, for development only):

  | Email | Password | Role |
  |---|---|---|
  | `user@example.com` | `password123` | user |
  | `admin@example.com` | `admin12345` | admin |

- **In the API code:** add `CurrentUserDep` (any signed-in user) or `AdminDep` / `Depends(require_admin)` to a route (`apps/api/src/api/core/auth.py`).
- **In Swagger** (`/docs`): call `POST /auth/login`. The browser stores the cookie and sends it on later requests.
- **In the web app:** pages and server actions call the API from the Next server, so the browser never talks to the API directly. On signup and signin, the server action copies the API's `session_id` cookie onto the browser (`saveSessionCookie` in `apps/web/src/lib/auth.ts`). Later calls pass the token back with the generated client's `auth` option, which sends it only to endpoints that declare the cookie scheme. The UI hides New/Edit/Delete from non-admins, but the API is what enforces the rule.

## Tests

`npm run test` runs the API tests against a separate `pycommerce_test` database, created automatically on the same Postgres. Each test runs inside a transaction that is rolled back, so tests never touch your dev data or each other (see `apps/api/tests/conftest.py`).

## Commit messages

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/), e.g. `feat(api): add products endpoint`. A husky `commit-msg` hook runs [commitlint](https://commitlint.js.org) (`@commitlint/config-conventional`) and rejects anything else. The hook is installed automatically by `npm install` (via the `prepare` script).

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on pull requests and on pushes to `main`:

| Job | What it checks |
|---|---|
| Commit messages | commitlint on every commit in the PR (or the pushed range on `main`) |
| Lint & typecheck | `turbo run lint typecheck`: Ruff + mypy for the API, ESLint + `tsc` for the web app and api-client |
| Tests | Applies migrations to a Postgres service container, then `turbo run test` |

The jobs share `.github/actions/setup`, which installs Node (version from `.nvmrc`), uv, and all dependencies from the lockfiles (`npm ci`, `uv sync --locked`). Out-of-date lockfiles fail CI. `package.json` requires npm `^11.13.0` through `devEngines`, and npm refuses to install with a version outside that range.

## How the API → frontend type pipeline works

```
apps/api (Python)  --api#openapi-->  apps/api/openapi.json
                   --api-client#generate-->  packages/api-client/src/client/*.gen.ts
                   --> apps/web imports { healthGetHealth } from "api-client"
```

- `web` depends on `api-client`, and its `dev`, `build` and `typecheck` tasks depend on `^generate`. So changing a Python route regenerates the schema and client before the frontend starts or typechecks.
- Both generated artifacts are gitignored. Turbo caches them and only regenerates when Python sources change.
- `npm run dev` generates the client once at startup. If you change API routes or schemas while it's running, run `npx turbo run generate`.
- SDK function names come from `<tag>-<function name>` (see `generate_operation_id` in `apps/api/src/api/main.py`). For example, `get_health` tagged `health` becomes `healthGetHealth`.

## Adding models

1. Create a model in `apps/api/src/api/models/` that subclasses `api.db.base.Base`.
2. Export it from `apps/api/src/api/models/__init__.py`. `migrations/env.py` imports that package, so autogenerate sees it.
3. Run `npm run db:revision -w api -- -m "..."`, review the file, then `npm run db:migrate`.

New migration files are run through Ruff automatically (see `[post_write_hooks]` in `apps/api/alembic.ini`).
