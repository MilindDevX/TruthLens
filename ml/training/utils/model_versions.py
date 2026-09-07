INVALID_TEXT_MODEL_VERSIONS = {"v1.0.0", "v1.1.0", "v1.2.0"}
EXPECTED_TRAINING_LABEL_MAPPING = {"0": "real", "1": "fake"}


def validate_release_metadata(metadata: dict) -> None:
    """Reject artifacts that lack the minimum serving evidence."""
    if metadata.get("training_label_mapping") != EXPECTED_TRAINING_LABEL_MAPPING:
        raise ValueError("training_label_mapping is missing or invalid")
    if metadata.get("ood_validation", {}).get("f1", 0) < 0.75:
        raise ValueError("ood_validation F1 is below the release gate")
    if not metadata.get("sklearn_version"):
        raise ValueError("sklearn_version is required")


def validate_text_model_version(version: str) -> None:
    if not version:
        raise ValueError("An explicit new model version is required.")
    if version in INVALID_TEXT_MODEL_VERSIONS:
        raise ValueError(f"{version} is invalid because its labels were reversed; use a new version.")
