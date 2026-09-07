# Model Accuracy Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent random/unavailable model responses, repair data-label provenance, and stop presenting a baseline as an ensemble.

**Architecture:** A strict dependency requires a loaded baseline before analysis or readiness succeeds. The dataset downloader owns the verified Hugging Face label mapping and provenance manifest. Training refuses legacy datasets without that manifest and writes only explicit new versions.

**Tech Stack:** FastAPI, pytest, pandas, Hugging Face Datasets, scikit-learn.

**Spec:** `docs/superpowers/specs/2026-09-06-model-accuracy-remediation-design.md`

## Global Constraints

- Do not add dependencies.
- Do not load, serve, or generate placeholder predictions when no baseline is available.
- Do not overwrite or publish `v1.0.0`; future training requires an explicit new version.
- Do not claim AI-authorship, an advanced model, or meta-model support unless their artifacts exist.
- Preserve existing untracked data, model, and log files.

---

### Task 1: Fail closed for unavailable baseline inference

**Files:**
- Create: `backend/tests/test_model_availability.py`
- Modify: `backend/app/ml/dependencies.py`
- Modify: `backend/app/content/router.py`
- Modify: `backend/app/content/service.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `request.app.state.text_inference`.
- Produces: `get_text_inference(request) -> TextInferenceService`, raising HTTP 503 unless `has_baseline` is true.

- [ ] **Step 1: Write failing dependency tests**

```python
from types import SimpleNamespace
from fastapi import HTTPException
import pytest

from app.ml.dependencies import get_text_inference


def request_for(service):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(text_inference=service)))


def test_requires_a_loaded_baseline():
    with pytest.raises(HTTPException) as error:
        get_text_inference(request_for(SimpleNamespace(has_baseline=False)))
    assert error.value.status_code == 503
    assert error.value.detail == "Text model unavailable. Try again later."


def test_returns_loaded_baseline_service():
    service = SimpleNamespace(has_baseline=True)
    assert get_text_inference(request_for(service)) is service
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_model_availability.py -q`

Expected: the no-baseline case fails because the current dependency accepts any non-`None` service.

- [ ] **Step 3: Implement minimal strict dependency and route**

```python
service = getattr(request.app.state, "text_inference", None)
if service is None or not service.has_baseline:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Text model unavailable. Try again later.",
    )
return service
```

Replace `get_text_inference_optional` in the analysis route with this dependency and make the parameter non-optional. Remove `_placeholder_prediction` and unreachable fallback branches from the service.

- [ ] **Step 4: Add failing readiness tests**

```python
from app.main import app, health_check


@pytest.mark.asyncio
async def test_health_is_unavailable_without_baseline():
    app.state.text_inference = SimpleNamespace(
        version="v1.0.0", has_baseline=False, has_advanced=False
    )
    response = await health_check()
    assert response.status_code == 503
    assert b'"status":"unavailable"' in response.body


@pytest.mark.asyncio
async def test_health_is_healthy_with_baseline():
    app.state.text_inference = SimpleNamespace(
        version="v1.1.0", has_baseline=True, has_advanced=False
    )
    response = await health_check()
    assert response["status"] == "healthy"
    assert response["models"]["text"]["has_baseline"] is True
```

- [ ] **Step 5: Run readiness tests to verify they fail**

Run: `cd backend && .venv/bin/python -m pytest tests/test_model_availability.py -q`

Expected: the unavailable readiness test fails because `/health` currently always returns `status: "healthy"`.

- [ ] **Step 6: Implement minimal readiness behavior**

```python
if text_inference is None or not text_inference.has_baseline:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "detail": "Text model unavailable. Try again later."},
    )
```

Retain the existing health payload for the healthy path. Ensure the unavailable response reports `status: "unavailable"` through a small response body rather than pretending readiness.

- [ ] **Step 7: Run focused tests, then backend suite**

Run: `cd backend && .venv/bin/python -m pytest tests/test_model_availability.py -q`

Expected: PASS.

Run: `cd backend && .venv/bin/python -m pytest -q`

Expected: PASS, or report existing environment-dependent integration-test failures separately.

### Task 2: Make source-label mapping and provenance testable

**Files:**
- Create: `ml/tests/test_download_data.py`
- Modify: `ml/scripts/download_data.py`

**Interfaces:**
- Consumes: an in-memory pandas frame with a `label` column.
- Produces: `split_labelled_articles(frame) -> tuple[DataFrame, DataFrame]`, ordered as `(real, fake)`, and `dataset_provenance.json` adjacent to downloaded CSVs.

- [ ] **Step 1: Write failing label-contract test**

```python
import pandas as pd

from ml.scripts.download_data import split_labelled_articles


def test_huggingface_label_contract_maps_one_to_real_and_zero_to_fake():
    records = pd.DataFrame({"label": [0, 1], "title": ["fake", "real"]})
    real, fake = split_labelled_articles(records)
    assert real["title"].tolist() == ["real"]
    assert fake["title"].tolist() == ["fake"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `ml/.venv/bin/python -m pytest ml/tests/test_download_data.py -q`

Expected: FAIL because `split_labelled_articles` does not exist.

- [ ] **Step 3: Implement minimal mapping and manifest**

```python
def split_labelled_articles(frame):
    return frame[frame["label"] == 1].copy(), frame[frame["label"] == 0].copy()
```

Call the helper before writing CSVs. Write `dataset_provenance.json` containing dataset ID, resolved revision from the loaded dataset metadata when available, and `{ "0": "fake", "1": "real" }`. Do not silently reuse existing `True.csv`/`Fake.csv` without that manifest.

- [ ] **Step 4: Add failing legacy-cache test**

```python
from pathlib import Path
import pytest

from ml.scripts.download_data import require_dataset_provenance


def test_legacy_csv_cache_without_provenance_is_rejected(tmp_path: Path):
    (tmp_path / "True.csv").write_text("title,text\nreal,text\n")
    (tmp_path / "Fake.csv").write_text("title,text\nfake,text\n")
    with pytest.raises(ValueError, match="dataset_provenance.json"):
        require_dataset_provenance(tmp_path)
```

- [ ] **Step 5: Run test to verify it fails**

Run: `ml/.venv/bin/python -m pytest ml/tests/test_download_data.py -q`

Expected: FAIL because the provenance guard does not exist.

- [ ] **Step 6: Implement provenance guard and run tests**

Implement `require_dataset_provenance(path)` with `Path(path) / "dataset_provenance.json"`; raise `ValueError` if missing or its label mapping differs from the verified contract.

Run: `ml/.venv/bin/python -m pytest ml/tests/test_download_data.py -q`

Expected: PASS.

### Task 3: Require provenance and new artifact versions in training

**Files:**
- Modify: `ml/scripts/train_baseline.py`
- Modify: `ml/training/text/train_baseline.py`
- Test: `ml/tests/test_download_data.py`

**Interfaces:**
- Consumes: `ml/data/isot/dataset_provenance.json` with verified mapping.
- Produces: a model metadata field containing dataset provenance; rejects `v1.0.0`.

- [ ] **Step 1: Write failing explicit-version test**

```python
import pytest

from ml.scripts.train_baseline import validate_training_version


def test_rejects_invalid_reversed_model_version():
    with pytest.raises(ValueError, match="v1.0.0 is invalid"):
        validate_training_version("v1.0.0")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `ml/.venv/bin/python -m pytest ml/tests/test_download_data.py -q`

Expected: FAIL because `validate_training_version` does not exist.

- [ ] **Step 3: Implement guards and metadata propagation**

```python
def validate_training_version(version: str) -> None:
    if version == "v1.0.0":
        raise ValueError("v1.0.0 is invalid because its labels were reversed; use a new version.")
```

Require a non-default `--version` argument in the training wrapper, call `require_dataset_provenance`, and pass the loaded manifest into `train_baseline`. Include it in saved `metadata.json`.

- [ ] **Step 4: Run focused tests**

Run: `ml/.venv/bin/python -m pytest ml/tests/test_download_data.py -q`

Expected: PASS.

### Task 4: Truthful serving copy and output semantics

**Files:**
- Modify: `backend/app/content/service.py`
- Modify: affected frontend result components after locating every `credibility`, `advanced`, `ensemble`, and `AI-generated` user-facing claim.
- Test: existing focused backend tests plus frontend check appropriate to package scripts.

**Interfaces:**
- Consumes: baseline model `probability` (`P(fake)`).
- Produces: one final baseline prediction when advanced is absent; UI labels it as a baseline fake-news estimate.

- [ ] **Step 1: Search all user-facing claims before editing**

Run: `rg -n -i "credibility|advanced|ensemble|AI-generated|AI content" frontend backend README.md`

Expected: enumerate every claim; edit only results and nearby descriptions affected by this scope.

- [ ] **Step 2: Write failing service test for baseline-only final prediction**

Add a focused test that supplies a baseline-only `prediction_result` and asserts the final prediction and displayed probability come from `baseline`, not a copied `advanced` result.

- [ ] **Step 3: Run test to verify it fails**

Run the focused backend test. Expected: FAIL because service currently makes `advanced` final unconditionally.

- [ ] **Step 4: Implement smallest truthful presentation**

Use baseline as final when no advanced artifact is present. Rename any class-confidence display to `P(fake)` and remove ensemble/meta-model claims from the changed views.

- [ ] **Step 5: Verify affected workflows**

Run focused backend tests and the frontend’s existing lint/build command. Render the affected result view at desktop and 375px; confirm no fabricated advanced/ensemble copy remains.

### Task 5: Local retraining gate (no publication)

**Files:**
- No source change unless a failing training/evaluation test reveals one.
- Create: `models/text/v1.1.0/*` locally only after all previous tasks pass.

- [ ] **Step 1: Regenerate source data**

Run: `rm` is not authorized. Instead move existing local CSV cache aside only after explicit confirmation, then run `ml/.venv/bin/python ml/scripts/download_data.py`.

- [ ] **Step 2: Train a distinct version**

Run: `ml/.venv/bin/python ml/scripts/train_baseline.py --version v1.1.0 --optuna-trials 30`

Expected: output includes corrected provenance and does not modify `v1.0.0`.

- [ ] **Step 3: Validate evidence**

Run the project evaluator and a small human-reviewed smoke set. Record held-out metrics, OOD result (or its explicit absence), and smoke cases before any artifact publication.

- [ ] **Step 4: Obtain separate approval before external publication/deployment**

Do not upload artifacts or change Render configuration without explicit approval.
