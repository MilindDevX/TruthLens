import sklearn
import pytest

from ml.training.text import train_baseline


def test_training_runtime_metadata_records_the_sklearn_version():
    assert train_baseline.training_runtime_metadata() == {
        "sklearn_version": sklearn.__version__
    }


@pytest.mark.parametrize("version", ["v1.0.0", "v1.1.0", "v1.2.0"])
def test_rejects_versions_with_invalid_or_failed_evidence(version):
    with pytest.raises(ValueError):
        train_baseline.validate_text_model_version(version)


def test_requires_an_explicit_new_model_version():
    with pytest.raises(ValueError, match="explicit new model version"):
        train_baseline.validate_text_model_version("")
