# Text model release checklist

Do not publish an artifact until every item is true.

- [ ] Output version is new and not `v1.0.0`, `v1.1.0`, or `v1.2.0`.
- [ ] `dataset_provenance.json` records source and training label mappings.
- [ ] Metadata records `training_label_mapping`, held-out LIAR F1, and `sklearn_version`.
- [ ] Held-out LIAR F1 is at least `0.75`.
- [ ] Ten reviewed smoke cases pass: five Reuters-like real items and five clickbait-style fake items.
- [ ] The deployment runtime uses the artifact's exact scikit-learn version.
- [ ] `/health` is confirmed healthy by both Render logs and an independent public request.

If any item fails, retain the artifact for investigation only. Do not upload or activate it.
