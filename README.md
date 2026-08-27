<div align="center">

# TruthLens 🔍

**AI Content Verification & Interpretability Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

*An end-to-end ML platform that detects AI-generated content with **91.3% F1-score**,<br/>
serves inference in **< 300ms** on CPU, and explains its reasoning through token-level heatmaps.*

<br/>

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [ML Pipeline](#-machine-learning-pipeline) · [Contributing](#-contributing)

</div>

---

## Why TruthLens?

Most AI-content detectors are black boxes — they tell you *what*, but never *why*. TruthLens is different:

- **Multi-Model Ensemble** — A baseline TF-IDF + Logistic Regression model runs alongside a fine-tuned DistilBERT, fused by a meta-model for robust credibility scoring.
- **Explainability-First** — SHAP, LIME, and attention-based token heatmaps show users exactly which words triggered the prediction.
- **Production-Grade** — Gunicorn + Uvicorn workers, asyncio-native database layer, JWT auth with refresh token rotation, rate limiting, structured JSON logging, and real-time drift monitoring.
- **Zero-Config Deployment** — One `docker compose up --build` spins up PostgreSQL, FastAPI, and an Nginx-served React SPA.

---

## ✨ Key Features

| Category | Feature |
|----------|---------|
| **Detection** | Binary classification (real vs. AI-generated) with 93.1% accuracy, 91.3% F1-score |
| **Inference** | < 300ms latency on CPU — no GPU required |
| **Explainability** | Token-level SHAP / LIME / attention heatmaps for every prediction |
| **Credibility Score** | Meta-model fuses baseline + advanced model outputs into a single 0–1 credibility score |
| **Auth** | JWT (access + refresh with rotation & compromise detection) + Google OAuth |
| **Drift Monitoring** | Rolling-window KL divergence, confidence tracking, and class-balance alerts |
| **Analysis History** | Paginated history with dedup caching — skip inference for identical inputs |
| **Admin Panel** | Dev-only admin routes for system inspection |
| **UI** | Glassmorphism React dashboard with credibility gauge, token heatmap, and model comparison |

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
                  │        │  ┌──────┐ ┌─────────┐ │ │
                  │        │  │TF-IDF│ │DistilBERT│ │ │
                  │        │  │ + LR │ │(PyTorch) │ │ │
                  │        │  └──┬───┘ └────┬─────┘ │ │
                  │        │     └────┬─────┘       │ │
                  │        │    Meta-Model Fusion    │ │
                  │        │    + SHAP / Attention   │ │
                  │        │    + Drift Monitor      │ │
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
│   │   │   ├── text_inference.py   # Dual-model inference service
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
│       ├── text_explainer.py   # SHAP + LIME + attention explainability
│       └── adversarial.py      # Adversarial robustness testing
├── docker-compose.yml          # Full-stack orchestration (4 services)
├── .env.docker                 # Production environment config
└── README.md
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **ML Model** | DistilBERT (`distilbert-base-uncased`) | Fine-tuned binary sequence classifier |
| **ML Baseline** | TF-IDF + Logistic Regression (scikit-learn) | Fast baseline predictions via joblib |
| **ML Framework** | PyTorch 2.5 | Model inference (CPU-optimized, `torch.no_grad()`) |
| **NLP** | Hugging Face Transformers | Tokenization + model serving |
| **Explainability** | SHAP 0.46, LIME 0.2 | Token-level feature attribution |
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
| `POST` | `/api/v1/analyze/text` | Analyze text for AI-generated content |

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
    "baseline": { "prediction": "fake", "confidence": 0.89 },
    "advanced": { "prediction": "fake", "confidence": 0.96 }
  },
  "credibility_score": 0.08,
  "explainability": {
    "type": "shap",
    "influential_tokens": [
      { "token": "advancement", "impact": 0.91 },
      { "token": "fundamentally", "impact": 0.85 },
      { "token": "landscape", "impact": 0.78 }
    ]
  },
  "disclaimer": "This is an AI-generated estimate. It does not replace professional fact-checking.",
  "model_version": "v1.0.0",
  "created_at": "2026-08-27T10:00:00Z"
}
```

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
- **10,000 balanced samples** — GPT-4 generated, Claude generated, and human-written text
- **Preprocessing:** Cleaning, tokenization, and truncation via Hugging Face `transformers`
- **Genres tested:** News articles, essays, casual text (bias/fairness evaluation)

### Model Architecture

| Model | Role | Details |
|-------|------|---------|
| **Baseline** | Fast first-pass | TF-IDF vectorizer + Logistic Regression (scikit-learn, loaded via joblib) |
| **Advanced** | High-accuracy | `distilbert-base-uncased` fine-tuned for binary sequence classification |
| **Meta-Model** | Score fusion | Combines baseline + advanced outputs into a single credibility score |

> **Why DistilBERT?** — 97% of BERT's performance, 60% faster, 40% smaller → enables sub-300ms CPU inference without GPU acceleration.

### Evaluation Metrics

| Metric | Score |
|--------|-------|
| **Accuracy** | 93.1% |
| **F1-Score** | 91.3% |
| **Precision & Recall** | Tracked independently (per-class) |
| **ROC-AUC** | Assessed during training |
| **Bias & Fairness** | Evaluated across news, essays, casual text genres |

### Explainability

TruthLens provides three explainability methods:

1. **SHAP** — Shapley value-based feature attribution showing each token's contribution to the prediction
2. **LIME** — Local surrogate model explanations for individual predictions
3. **Attention Weights** — DistilBERT attention head visualizations

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
| `ACTIVE_TEXT_MODEL_VERSION` | `v1.0.0` | Active text model version |
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
| **Startup** | Eager model loading → zero cold-start |
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

**Built with ❤️ and a healthy skepticism of AI-generated text.**

</div>
