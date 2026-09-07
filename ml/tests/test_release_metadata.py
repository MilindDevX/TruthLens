import pytest

from ml.training.utils.model_versions import validate_release_metadata


def test_rejects_release_metadata_without_required_evidence():
    with pytest.raises(ValueError, match="sklearn_version"):
        validate_release_metadata(
            {
                "training_label_mapping": {"0": "real", "1": "fake"},
                "ood_validation": {"f1": 0.8},
            }
        )
