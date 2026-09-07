<div align="center">

# TruthLens 🔍

**Fake-News Classification & Interpretability Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

*A fake-news classification platform with fail-closed serving and token-level SHAP explanations.*

<br/>

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [ML Pipeline](#-machine-learning-pipeline) · [Contributing](#-contributing)

</div>

---

## Why TruthLens?

TruthLens classifies fake-news signals and exposes the baseline model’s reasoning:

- **Baseline Classifier** — TF-IDF + Logistic Regression provides the current fake-news classification result.
- **Explainability-First** — SHAP token attribution shows which terms influenced a baseline prediction.
- **Production-Grade** — Gunicorn + Uvicorn workers, asyncio-native database layer, JWT auth with refresh token rotation, rate limiting, structured JSON logging, and real-time drift monitoring.
- **Zero-Config Deployment** — One `docker compose up --build` spins up PostgreSQL, FastAPI, and an Nginx-served React SPA.

---

## ✨ Key Features

| Category | Feature |
|----------|---------|
| **Detection** | Binary fake-news classification (real vs. fake) plus published fact-check lookup |
| **Serving safety** | Returns 503 rather than a result when no valid baseline is loaded |
| **Explainability** | Token-level SHAP attribution for baseline predictions |
| **Probability** | Displays the selected model’s estimated P(real) |
| **Auth** | JWT (access + refresh with rotation & compromise detection) + Google OAuth |
| **Drift Monitoring** | Rolling-window KL divergence, confidence tracking, and class-balance alerts |
| **Analysis History** | Paginated history with dedup caching — skip inference for identical inputs |
| **Admin Panel** | Dev-only admin routes for system inspection |
| **UI** | React dashboard with P(real), token heatmap, model detail, and fact-check evidence |

---

## 🏗 Architecture

```
                  ┌──────────────────────────────────┐
                  │       React SPA (Nginx :80)      │
                  │  Tailwind CSS · Glassmorphism UI  │
                  └──────────────┬───────────────────┘
                                 │  /api/v1/*
                  ┌──────────────▼───────────────────┐
                  │   FastAPI + Gunicorn (Uvicorn     │
                  │        Workers :8000)             │
                  │                                   │
                  │  ┌─────────┐  ┌───────────────┐  │
                  │  │ Auth    │  │ Content       │  │
                  │  │ JWT/OAuth│ │ Analysis      │  │
                  │  └─────────┘  └───────┬───────┘  │
                  │                       │          │
                  │        ┌──────────────▼────────┐ │
                  │        │  TextInferenceService  │ │
                  │        │  ┌───────────────┐      │ │
                  │        │  │ TF-IDF +       │      │ │
                  │        │  │ Logistic       │      │ │
                  │        │  │ Regression     │      │ │
                  │        │  └───────┬───────┘      │ │
                  │        │      SHAP + Drift       │ │
                  │        └────────────────────────┘ │
                  └──────────────┬───────────────────┘
                                 │
                  ┌──────────────▼───────────────────┐
                  │     PostgreSQL 16 Alpine (:5432)  │
                  │        (async via asyncpg)        │
                  └──────────────────────────────────┘
```

### Project Structure

```
TruthLens/
├── backend/
│   ├── app/
│   │   ├── admin/              # Dev-only admin routes
│   │   ├── auth/               # JWT + Google OAuth + refresh rotation
│   │   ├── content/            # Text analysis endpoint + schemas
│   │   ├── history/            # Paginated analysis history
│   │   ├── middleware/         # Rate limiter, structured logging
│   │   ├── ml/
│   │   │   ├── text_inference.py   # Baseline inference; advanced only when its artifact exists
│   │   │   ├── drift_monitor.py    # KL divergence + confidence tracking
│   │   │   ├── model_loader.py     # Eager model loading at startup
│   │   │   └── dependencies.py     # FastAPI DI for ML services
│   │   ├── users/              # User models & CRUD
│   │   ├── config.py           # Pydantic BaseSettings
│   │   ├── database.py         # Async SQLAlchemy engine + sessions
│   │   └── main.py             # App factory + lifecycle manager
│   ├── alembic/                # Database migrations
│   ├── tests/
│   │   ├── test_integration.py # Full API integration tests
│   │   └── test_load.py        # Load testing
│   ├── gunicorn.conf.py        # Production-grade Gunicorn config
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # Landing, Dashboard, Login, Register, History, AnalysisDetail
│   │   ├── components/         # TokenHeatmap, CredibilityGauge, ModelComparison, Navbar, etc.
│   │   ├── auth/               # Auth context + guards
│   │   └── api/                # Axios API client
│   ├── nginx.conf              # Production Nginx with API reverse proxy
│   ├── Dockerfile
│   └── package.json
├── ml/
│   ├── training/               # Model training scripts
│   └── explainability/
│       ├── text_explainer.py   # Explainability utilities
│       └── adversarial.py      # Adversarial robustness testing
├── docker-compose.yml          # Full-stack orchestration (4 services)
├── .env.docker                 # Production environment config
└── README.md
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **ML Model** | TF-IDF + Logistic Regression (scikit-learn) | Baseline fake-news classifier via joblib |
| **Explainability** | SHAP 0.46 | Token-level baseline feature attribution |
| **Backend** | FastAPI 0.115, Gunicorn, Uvicorn | Async ASGI with production workers |
| **Database** | PostgreSQL 16 + SQLAlchemy 2.0 + asyncpg | Async ORM with Alembic migrations |
| **Auth** | python-jose (JWT), passlib (bcrypt) | Access + refresh tokens, Google OAuth |
| **Frontend** | React 19, Tailwind CSS, Vite 7 | Glassmorphism SPA with React Router |
| **Infrastructure** | Docker, Docker Compose, Nginx | Zero-config containerized deployment |
| **Monitoring** | Custom drift monitor, structlog | KL divergence, JSON structured logging |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docker.com) and Docker Compose

### One-Command Deployment

```bash
# Clone
git clone https://github.com/MilindDevX/TruthLens.git
cd TruthLens

# Start everything (PostgreSQL + Backend + Frontend)
docker compose up --build
```

| Service | URL |
|---------|-----|
| **Frontend Dashboard** | [http://localhost](http://localhost) |
| **API (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **API (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) |

> **Dev Mode** — To include pgAdmin for database management:
> ```bash
> docker compose --profile dev up --build
> ```
> pgAdmin will be available at [http://localhost:5050](http://localhost:5050).

### Local Development (Without Docker)

<details>
<summary><strong>Backend</strong></summary>

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database URL and JWT secret

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

</details>

<details>
<summary><strong>Frontend</strong></summary>

```bash
cd frontend

# Install dependencies (pnpm required)
pnpm install

# Start development server
pnpm run dev
# → http://localhost:5173
```

</details>

---

## 📊 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register with email + password |
| `POST` | `/api/v1/auth/login` | Login, returns JWT access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token (compromise detection) |
| `GET` | `/api/v1/auth/google` | Redirect to Google OAuth consent screen |
| `GET` | `/api/v1/auth/google/callback` | Google OAuth callback handler |

### Content Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/text` | Analyze news text for fake-news signals |
| `POST` | `/api/v1/analyze/fact-check` | Look up a published ClaimReview fact check |

**Request:**
```json
{
  "text": "The rapid advancement of artificial intelligence has fundamentally altered the technological landscape..."
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "content_type": "text",
  "prediction": "fake",
  "confidence": 0.94,
  "low_confidence_flag": false,
  "model_scores": {
    "baseline": { "prediction": "fake", "confidence": 0.89 }
  },
  "credibility_score": 0.08,
  "evidence_priority": "published_fact_check",
  "fact_check": {
    "status": "matched",
    "claim": "A related published claim",
    "rating": "False",
    "publisher": "Example fact-checker",
    "url": "https://example.com/review"
  },
  "explainability": {
    "type": "shap",
    "influential_tokens": [
      { "token": "advancement", "impact": 0.91 },
      { "token": "fundamentally", "impact": 0.85 },
      { "token": "landscape", "impact": 0.78 }
    ]
  },
  "disclaimer": "This is a model estimate. It does not replace professional fact-checking.",
  "model_version": "v1.3.0",
  "created_at": "2026-08-27T10:00:00Z"
}
```

`evidence_priority` is `published_fact_check` when a related ClaimReview is found. In that case, the publisher's review is the primary evidence and the classifier output remains a secondary estimate. `model_estimate` means no published review was available; it is not a truth verdict.

### Analysis History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/history` | Paginated analysis history for authenticated user |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check with model status + drift stats |

---

## 🧠 Machine Learning Pipeline

### Dataset
- **ISOT fake-news data** — corrected label mapping is required before training.
- **Preprocessing:** TF-IDF baseline cleaning, stopword removal, and lemmatization.
- **Evaluation:** retraining must produce fresh held-out and smoke-set evidence before deployment.
- **Fact checks:** `matched` links a published review; `not_found` and `unavailable` are not truth verdicts.

### Model Architecture

| Model | Role | Details |
|-------|------|---------|
| **Baseline** | Current classifier | TF-IDF vectorizer + Logistic Regression (scikit-learn, loaded via joblib) |

> **Model availability:** the server rejects analysis requests when no valid baseline artifact is loaded.

### Evaluation Metrics

| Metric | Score |
|--------|-------|
| **Current deployment (interim)** | `v1.0.0`; it has reversed labels and is not a validated production artifact |
| **Replacement artifact** | Requires corrected-data held-out, OOD, and smoke-set results before deployment |

### Explainability

TruthLens provides SHAP feature attribution for the baseline model, showing each token's contribution to its prediction.

### Drift Monitoring

A lightweight, non-blocking production monitor tracks:
- **KL Divergence** — Between training confidence distribution and rolling production predictions
- **Mean Confidence** — Alerts on sudden confidence drops (distribution shift)
- **Class Balance** — Detects positive-rate drift (imbalanced production data)

Alerts fire via structured JSON logs when thresholds are exceeded — without slowing inference.

---

## ⚙️ Configuration

### Environment Variables

<details>
<summary><strong>View all configuration options</strong></summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | SQLite (dev) | Async DB connection string |
| `JWT_SECRET_KEY` | — | **⚠️ Change in production!** Generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `GOOGLE_CLIENT_ID` | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth client secret |
| `RATE_LIMIT_PER_MINUTE` | `60` | API rate limit per user |
| `MAX_TEXT_WORDS` | `5000` | Max text input (words) |
| `MAX_TEXT_CHARS` | `30000` | Max text input (characters) |
| `MAX_IMAGE_SIZE_MB` | `10` | Max image upload size |
| `ACTIVE_TEXT_MODEL_VERSION` | Set explicitly | Set only to a validated artifact; `v1.0.0`, `v1.1.0`, and `v1.2.0` are retired |
| `FACT_CHECK_API_KEY` | — | Server-only Google Claim Search key; enables published-review lookup |
| `JWT_SECRET_KEY` | — | Required in production; the backend refuses its development default |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `localhost:5173,3000` | Allowed CORS origins |
| `GUNICORN_WORKERS` | `4` (capped) | Worker count (auto-tuned to CPU cores) |

</details>

---

## 🧪 Testing

```bash
cd backend
source .venv/bin/activate

# Integration tests
pytest tests/test_integration.py -v

# Load tests
pytest tests/test_load.py -v
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Inference Latency** | < 300ms (CPU, no GPU) |
| **Frontend Build** | ~860ms (112 modules, Vite 7) |
| **Production Bundle** | 312 KB JS (100 KB gzipped) + 27 KB CSS |
| **Startup** | Models load at startup; startup time includes model download and deserialization |
| **Concurrency** | Gunicorn multi-worker + async SQLAlchemy |

---

## 🗺 Roadmap

- [ ] **Image Analysis** — Grad-CAM explainability for manipulated image detection
- [ ] **Multimodal Fusion** — Combined text + image credibility scoring
- [ ] **A/B Model Testing** — Live model comparison in production
- [ ] **Webhook Alerts** — Real-time drift notifications to Slack / Discord
- [ ] **Browser Extension** — One-click content verification from any webpage

---

## 👨‍💻 Author

**Milind Bansal**
Machine Learning Engineer & Full-Stack Developer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Milind_Bansal-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/milind-bansal-177606244/)
[![GitHub](https://img.shields.io/badge/GitHub-MilindDevX-181717?style=flat&logo=github)](https://github.com/MilindDevX)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ and healthy skepticism.**

</div>
