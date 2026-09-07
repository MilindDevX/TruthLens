# TruthLens frontend

React 19 + Vite dashboard for text analysis, model estimates, token explanations, and published fact-check evidence.

## Run locally

```bash
pnpm install
pnpm dev
```

The app calls `http://localhost:8000/api/v1` by default. Set `VITE_API_URL` to a backend origin for another environment; `/api/v1` is appended automatically when omitted.

```bash
pnpm build
pnpm lint
```

Do not put API keys in frontend environment variables. Fact-check requests are made by the authenticated backend.
