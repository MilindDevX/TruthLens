# TruthLens 🔍

**AI Content Verification & Interpretability System**

TruthLens is an end-to-end Machine Learning platform designed to detect AI-generated content and assess credibility. It achieves a **91.3% F1-score** using fine-tuned DistilBERT models, serving inference in **< 300ms** via a highly concurrent, fully Dockerized FastAPI architecture.

Unlike black-box detection tools, TruthLens features an interpretability dashboard with token-level confidence heatmaps, letting users understand exactly *why* text was flagged.

---

## 🚀 Key Features

- **High-Accuracy Detection:** Classifies human vs. AI-generated text with 93.1% accuracy.
- **Ultra-Fast Inference:** FastAPI backend processes requests in under 300ms on CPU without requiring GPU acceleration.
- **Token Heatmaps:** Visual interpretability showing which specific words/tokens strongly indicate AI generation.
- **Fully Containerized:** Zero-config deployment using Docker Compose (PostgreSQL, FastAPI, React).
- **Comprehensive Evaluation:** Rigorously tested against a balanced 10,000-sample dataset comprising GPT-4, Claude, and human-written text.

---

## 🧠 Machine Learning Pipeline

TruthLens follows a rigorous ML development lifecycle to ensure high reliability and mitigate bias:

### 1. Data Processing
- **Dataset:** Balanced 10,000-sample dataset.
- **Preprocessing:** Cleaning, tokenization, and truncation via Hugging Face `transformers`.

### 2. Model Architecture
- **Base Model:** `distilbert-base-uncased` fine-tuned for binary sequence classification.
- **Why DistilBERT?** Provides 97% of BERT's performance while being 60% faster and 40% smaller, enabling our sub-300ms CPU inference goal.

### 3. Evaluation Metrics
We compute and log the following metrics to ensure model fairness and performance:
- **Accuracy:** 93.1%
- **F1-Score:** 91.3%
- **Precision & Recall:** Tracked independently to balance false positives vs. false negatives.
- **ROC-AUC & Confusion Matrix:** Utilized during model training to assess threshold performance.
- **Bias & Fairness:** Evaluated across different text genres (news, essays, casual) to ensure uniform detection capability.

---

## 🏗 System Architecture

The application is built using a decoupled microservices architecture:

```
TruthLens/
├── backend/                  # FastAPI inference service (Python)
├── frontend/                 # React interpretation dashboard
├── ml/                       # Training, preprocessing & explainability scripts
└── docker-compose.yml        # Orchestration
```

### Tech Stack
- **ML & NLP:** PyTorch, Hugging Face Transformers, scikit-learn
- **Backend:** FastAPI, Python, Uvicorn
- **Frontend:** React, Tailwind CSS (Glassmorphism UI)
- **Infrastructure:** Docker, Docker Compose, PostgreSQL

---

## ⚙️ Setup & Installation

### Prerequisites
- Docker and Docker Compose installed on your machine.

### Quick Start (Dockerized)

The easiest way to run TruthLens is via Docker Compose, which spins up the database, backend, and frontend simultaneously.

1. Clone the repository:
   ```bash
   git clone https://github.com/MilindDevX/TruthLens.git
   cd TruthLens
   ```

2. Start the services:
   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - **Frontend Dashboard:** `http://localhost:3000`
   - **FastAPI Docs (Swagger):** `http://localhost:8000/docs`

---

## 📊 API Usage

The FastAPI backend exposes endpoints for fast inference.

**Endpoint:** `POST /api/v1/predict`
```json
// Request
{
  "text": "The rapid advancement of artificial intelligence has fundamentally altered the technological landscape..."
}

// Response
{
  "prediction": "AI-GENERATED",
  "confidence": 0.94,
  "inference_time_ms": 245,
  "tokens": [
    {"word": "rapid", "score": 0.8},
    {"word": "advancement", "score": 0.9}
  ]
}
```

---

## 👨‍💻 Author

**Milind Bansal**  
Machine Learning Engineer & Full-Stack Developer  
[LinkedIn](https://www.linkedin.com/in/milind-bansal-177606244/) | [GitHub](https://github.com/MilindDevX)
