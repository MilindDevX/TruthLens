# Model Accuracy Remediation Design

## Goal

Stop misleading analysis results immediately, correct the inverted fake-news training labels, and make retraining reproducible before another model artifact is deployed.

## Scope

### 1. Fail closed when no baseline model is available

`POST /api/v1/analyze/text` must return HTTP 503 with `"Text model unavailable. Try again later."` if no baseline model is loaded. It must not generate placeholder predictions, return cached placeholder results, or write analysis history.

`GET /health` is a readiness endpoint: return HTTP 200 and `status: "healthy"` only when a baseline model is loaded; otherwise return HTTP 503 and `status: "unavailable"`. Advanced models remain optional.

### 2. Correct the dataset label contract

The downloader currently maps the Hugging Face `GonzaloA/fake_news` labels backwards. The verified contract is:

- label `0`: fake / unreliable source → `Fake.csv`
- label `1`: real / Reuters source → `True.csv`

The download artifact must preserve the source dataset revision and label mapping. Legacy cached data without that provenance must not be used to train a new model.

### 3. Retire the invalid artifact and make retraining explicit

`v1.0.0` is invalid because it was trained with reversed semantic labels. No code path will silently treat it as a valid production artifact. The corrected pipeline produces a new version such as `v1.3.0` only after fresh data download, evaluation, and smoke checks. Versions `v1.0.0`, `v1.1.0`, and `v1.2.0` are retired and must not serve predictions.

Required pre-deployment evidence:

- held-out metrics from the corrected data;
- the existing LIAR evaluation, if available, recorded as different-task OOD evidence;
- a small human-reviewed smoke set, including Reuters-like real text and clickbait-style fake text;
- a `/health` response showing `has_baseline: true` from the target deployment.

### 4. Accurate product presentation

Until a separately trained AI-authorship model exists, this model is presented as a **fake-news classifier**, not an AI-generated-content detector. A matching published ClaimReview is the primary user-facing evidence; the classifier output is a secondary estimate and cannot override that review. Baseline output is shown as baseline-only. An advanced score or meta-model score must not be fabricated from the baseline.

## Architecture

The dependency boundary is the single enforcement point: the text-analysis route requires a usable baseline service. This keeps model-unavailable requests out of validation, cache, and persistence. Readiness uses the same capability check, so the deployment platform cannot route traffic to placeholder inference.

The data downloader owns source label mapping and provenance. Training consumes only provenance-bearing data and outputs a new versioned artifact; it does not overwrite the invalid artifact.

## Files Expected to Change

- `backend/app/ml/dependencies.py` — reject missing/unusable baseline service with HTTP 503.
- `backend/app/content/router.py` — require the strict inference dependency.
- `backend/app/content/service.py` — remove placeholder/random prediction path and false advanced-as-final behavior.
- `backend/app/main.py` — make health model-ready only with a baseline.
- `ml/scripts/download_data.py` — correct label mapping and save provenance.
- `ml/training/utils/data_loader.py` — reject legacy/unprovenanced data.
- `ml/training/text/train_baseline.py` — require explicit, new output version and record provenance.
- Focused backend and ML regression tests.
- User-facing copy that currently claims AI-authorship detection or an ensemble, where present.

## Acceptance Criteria

- Given no baseline service, when a text-analysis request arrives, then it receives 503 and no analysis record is created.
- Given a loaded baseline service, when `/health` is called, then it returns 200 with `has_baseline: true`.
- Given no baseline, when `/health` is called, then it returns 503 with `status: "unavailable"`.
- Given source label `0`, when data is downloaded, then it is stored as fake; label `1` is stored as real.
- Given cached data without the new provenance metadata, when training begins, then training refuses it.
- Given a new artifact, when it is proposed for deployment, then it has the corrected-label evaluation and smoke-set results documented.

## Out of Scope

- Training or shipping an AI-authorship classifier. It requires a separate, representative labeled dataset and evaluation plan.
- Creating the currently missing advanced DistilBERT and meta-model artifacts.
- Publishing model artifacts or deploying externally; those need separate approval after local validation.
