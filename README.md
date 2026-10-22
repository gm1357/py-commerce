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
| Regenerate the TS client by hand | `npx turbo run generate` |

API docs: http://localhost:8000/docs

## Commit messages

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/), e.g. `feat(api): add products endpoint`. A husky `commit-msg` hook runs [commitlint](https://commitlint.js.org) (`@commitlint/config-conventional`) and rejects anything else. The hook is installed automatically by `npm install` (via the `prepare` script).

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on pull requests and on pushes to `main`:

| Job | What it checks |
|---|---|
| Commit messages | commitlint on every commit in the PR (or the pushed range on `main`) |
| Lint & typecheck | `turbo run lint typecheck`: Ruff + mypy for the API, ESLint + `tsc` for the web app and api-client |
| Tests | Applies migrations to a Postgres service container, then `turbo run test` |

The jobs share `.github/actions/setup`, which installs Node (version from `.nvmrc`), the exact npm version pinned in `package.json` (`devEngines`), uv, and all dependencies from the lockfiles (`npm ci`, `uv sync --locked`). Out-of-date lockfiles fail CI.

## How the API → frontend type pipeline works

```
apps/api (Python)  --api#openapi-->  apps/api/openapi.json
                   --api-client#generate-->  packages/api-client/src/client/*.gen.ts
                   --> apps/web imports { healthGetHealth } from "api-client"
```

- `web` depends on `api-client`, and its `dev`, `build` and `typecheck` tasks depend on `^generate`. So changing a Python route regenerates the schema and client before the frontend starts or typechecks.
- Both generated artifacts are gitignored. Turbo caches them and only regenerates when Python sources change.
- SDK function names come from `<tag>-<function name>` (see `generate_operation_id` in `apps/api/src/api/main.py`). For example, `get_health` tagged `health` becomes `healthGetHealth`.

## Adding models

1. Create models that subclass `api.db.base.Base`.
2. Import them in `apps/api/migrations/env.py` so autogenerate sees them.
3. Run `npm run db:revision -w api -- -m "..."`, review the file, then `npm run db:migrate`.

New migration files are run through Ruff automatically (see `[post_write_hooks]` in `apps/api/alembic.ini`).
