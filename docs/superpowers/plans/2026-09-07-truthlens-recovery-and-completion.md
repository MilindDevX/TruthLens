# TruthLens Recovery and Completion Plan

> **For agentic workers:** Execute inline and sequentially. Preserve unrelated dirty files. Do not commit, push, upload models, alter Render, or alter Neon until the final approval batch.

**Goal:** Stop misleading predictions, make published fact evidence the primary user-facing result, create a reproducible fallback model path, harden deployment verification, and finish the approved homepage redesign.

**Architecture:** Serving is evidence-first: a published ClaimReview match is presented before any classifier estimate. The fallback classifier is fail-closed unless its artifact passes provenance, evaluation, and runtime-compatibility checks. Training and serving share one explicit artifact contract.

**Tech Stack:** FastAPI, pytest, scikit-learn, pandas, React 19, Vite, Tailwind, Render, Neon.

**Spec:** `docs/superpowers/specs/2026-09-06-model-accuracy-remediation-design.md`; approved Industrial Telemetry homepage direction.

## Global Constraints

- Keep local work safe for an 8GB M3 Pro: no heavyweight local retraining or parallel model processes.
- Do not serve `v1.0.0`; its semantic labels were reversed.
- Do not publish `v1.1.0` or `v1.2.0`; their LIAR gate failed.
- A no-match fact-check result is not a truth verdict.
- A classifier never overrides or re-labels a published fact check.
- Do not expose secrets in code, docs, logs, or commits.
- Only platform logs plus an independent public request may declare production unhealthy.

---

### Task 1: Make production serving fail closed

**Files:**
- Modify: `backend/app/ml/dependencies.py`, `backend/app/content/router.py`, `backend/app/content/service.py`, `backend/app/main.py`
- Test: `backend/tests/test_model_availability.py`, `backend/tests/test_content_service.py`

**Interfaces:**
- Consumes: `request.app.state.text_inference`.
- Produces: `get_text_inference(request) -> TextInferenceService`, or HTTP 503 with `Text model unavailable. Try again later.`

- [ ] Write tests for missing and baseline-less inference services, asserting 503 from analysis and health endpoints.
- [ ] Run the new tests and record their initial failure.
- [ ] Require `has_baseline` in `get_text_inference`; remove all placeholder prediction branches; make `/health` return 503 with `status: unavailable` when baseline is absent.
- [ ] Add a baseline-only service test proving final prediction, confidence, and P(real) use `prediction_result["baseline"]`.
- [ ] Run focused backend tests, then the backend suite; record unrelated environment failures separately.

### Task 2: Enforce one model artifact contract

**Files:**
- Modify: `backend/app/ml/model_loader.py`, `backend/app/config.py`, `backend/requirements.txt`, `backend/scripts/download_models.py`
- Modify: `ml/training/text/train_baseline.py`, `ml/training/utils/model_versions.py`
- Test: `backend/tests/test_model_availability.py`, `ml/tests/test_model_versions.py`

**Interfaces:**
- Consumes: artifact `metadata.json`.
- Produces: accepted artifacts only when `training_label_mapping == {"0":"real","1":"fake"}`, LIAR F1 is at least `0.75`, and `sklearn_version` matches the runtime.

- [ ] Write failing metadata tests for reversed labels, LIAR F1 below `0.75`, and a mismatched scikit-learn version.
- [ ] Run those tests to prove the current loader accepts unsafe metadata or version mismatches.
- [ ] Save `sklearn.__version__` in training metadata and validate it before `joblib.load`.
- [ ] Pin the backend scikit-learn dependency to the version used by the next validated artifact; do not pin to legacy `v1.0.0` merely to keep it serving.
- [ ] Make model download logs say `model unavailable` rather than `placeholder mode`.
- [ ] Run focused loader tests and a local model-load smoke test without training.

### Task 3: Repair source provenance and training entry points

**Files:**
- Modify: `ml/scripts/download_data.py`, `ml/training/utils/data_loader.py`, `ml/scripts/train_baseline.py`, `ml/training/text/train_baseline.py`
- Test: `ml/tests/test_download_data.py`, `ml/tests/test_model_versions.py`

**Interfaces:**
- Consumes: Hugging Face labels `0=fake`, `1=real`.
- Produces: `dataset_provenance.json` with both `source_label_mapping={"0":"fake","1":"real"}` and `training_label_mapping={"0":"real","1":"fake"}`.

- [ ] Write failing tests for `split_labelled_articles`, legacy cache rejection, and provenance keys consumed by `load_isot_dataset`.
- [ ] Run them and confirm the current downloader writes the incompatible `label_mapping` key.
- [ ] Write both mapping keys from the downloader, reject caches without the manifest, and make the training wrapper validate provenance even when CSV files already exist.
- [ ] Require a new explicit version and reject `v1.0.0`, `v1.1.0`, and `v1.2.0` as output targets.
- [ ] Run all ML provenance/version tests using the existing `ml/.venv`; do not download or train yet.

### Task 4: Produce evidence for a replacement model without using the laptop as a trainer

**Files:**
- Create: `ml/docs/model-release-checklist.md`
- Create: `ml/tests/test_release_metadata.py`
- Modify: `ml/training/text/train_baseline.py`

**Interfaces:**
- Consumes: fresh provenance-bearing data and an explicit version such as `v1.3.0`.
- Produces: artifact metadata containing held-out results, LIAR results, smoke-set results, data revision, label mappings, and scikit-learn version.

- [ ] Write a failing release-metadata test that rejects an artifact missing any required evidence field.
- [ ] Run it, then add the smallest metadata schema check in the training output path.
- [ ] Define a smoke set of ten reviewed examples: five Reuters-like real items and five clickbait-style fake items; record expected labels and model outcomes without copying full source text into logs.
- [ ] Use an external CPU runner for training. Run one bounded baseline experiment first; stop if held-out or LIAR F1 is below `0.75`.
- [ ] If it fails, do not tune indefinitely: switch to selecting a better matched, licensed fake-news training source and document its label contract before retraining.
- [ ] Run the release-metadata test and evaluator; retain artifacts locally or in the approved model store only after the final approval batch.

### Task 4A: Make fact evidence the primary analysis result

**Files:**
- Modify: `backend/app/content/service.py`, `backend/app/content/schemas.py`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/FactCheckEvidence.jsx`
- Test: `backend/tests/test_fact_check.py`, `frontend/src/utils/factCheckPresentation.test.js`

**Interfaces:**
- Consumes: ClaimReview lookup status and the fallback model result.
- Produces: a response that preserves fact-check source, rating, and URL; model output remains explicitly secondary and cannot contradict the cited review.

- [ ] Write failing tests proving a matched review is displayed as published evidence ahead of the model estimate.
- [ ] Add an explicit response field identifying evidence priority as `published_fact_check` or `model_estimate`.
- [ ] Render ClaimReview publisher, rating, and source URL prominently; render no verdict for `not_found` or `unavailable`.
- [ ] Run backend and frontend fact-check tests plus a signed-in workflow check.

### Task 5: Finish the approved Industrial Telemetry homepage

**Files:**
- Modify: `frontend/src/pages/Landing.jsx`, `frontend/src/index.css`, `frontend/tailwind.config.js`
- Create: `frontend/src/components/TelemetryPanel.jsx`
- Test: `frontend/src/pages/Landing.test.jsx` or existing lightweight component test harness

**Interfaces:**
- Consumes: current auth state and existing Tailwind design tokens.
- Produces: responsive homepage with the approved industrial telemetry visual language, reduced-motion-safe animation, and unchanged auth CTA routing.

- [ ] Capture the existing landing-page CTA destination and keyboard behavior in a failing component test.
- [ ] Build the telemetry panel from CSS and existing components; add no animation dependency.
- [ ] Use only transform/opacity animation, honor `prefers-reduced-motion`, and avoid autoplay media.
- [ ] Test CTA routing, run lint/build, and inspect desktop plus 375px rendering before staging.

### Task 6: Verify the fact-check workflow and operational health

**Files:**
- Modify: `backend/tests/test_fact_check.py`, `README.md`
- Create: `scripts/verify-production.sh`

**Interfaces:**
- Consumes: a public base URL and no secret values.
- Produces: an explicit `healthy`, `unhealthy`, or `inconclusive` result; `inconclusive` is never reported as an outage.

- [ ] Write a test for fact-check `matched`, `not_found`, and `unavailable` UI semantics.
- [ ] Add a shell verifier that checks HTTP status and JSON health payload, printing `inconclusive` for network timeouts.
- [ ] Verify live status using both Render logs and the public URL after deployment; record no secrets.
- [ ] Confirm a signed-in user sees a published review link when available and an honest no-match message otherwise.

### Task 7: Final quality gate and approval bundle

**Files:**
- Modify only files changed by Tasks 1–6.

- [ ] Run focused backend, ML, and frontend tests; run `pnpm run build`; inspect all staged diffs for secrets and unrelated changes.
- [ ] Verify no secret file is tracked and no API key pattern appears outside ignored secret folders.
- [ ] Produce one approval bundle covering: commit/push safety changes, deploy fail-closed serving, external training, artifact upload, and switching Render to a validated version.
- [ ] After approval, execute the approved external actions in order: deploy fail-closed code, train/evaluate externally, upload only a passing artifact, set its explicit version, deploy, then verify with logs plus public health.

## Completion Criteria

- The application never returns a prediction from an invalid or runtime-incompatible artifact.
- A replacement model has provenance, compatible runtime metadata, held-out metrics, LIAR F1 at least `0.75`, and smoke-set evidence.
- Fact-check evidence is distinct from model prediction and works for authenticated users.
- The homepage matches the approved direction, works at desktop and 375px, and honors reduced motion.
- Production health is confirmed by two independent signals after every deployment.
