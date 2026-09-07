from pathlib import Path

import pandas as pd
import pytest

from ml.scripts import train_baseline
from ml.training.utils.data_loader import load_isot_dataset, load_liar_dataset
from ml.training.utils.model_versions import validate_text_model_version


def test_rejects_invalid_reversed_model_version():
    with pytest.raises(ValueError, match="v1.0.0 is invalid"):
        train_baseline.validate_training_version("v1.0.0")


def test_shared_version_guard_rejects_invalid_model_version():
    with pytest.raises(ValueError, match="v1.0.0 is invalid"):
        validate_text_model_version("v1.0.0")


def test_training_data_without_provenance_is_rejected(tmp_path: Path):
    pd.DataFrame({"title": ["real"], "text": ["report"], "subject": ["news"]}).to_csv(
        tmp_path / "True.csv", index=False
    )
    pd.DataFrame({"title": ["fake"], "text": ["claim"], "subject": ["news"]}).to_csv(
        tmp_path / "Fake.csv", index=False
    )

    with pytest.raises(ValueError, match="dataset_provenance.json"):
        load_isot_dataset(tmp_path)


def test_training_data_with_wrong_label_mapping_is_rejected(tmp_path: Path):
    pd.DataFrame({"title": ["real"], "text": ["report"], "subject": ["news"]}).to_csv(
        tmp_path / "True.csv", index=False
    )
    pd.DataFrame({"title": ["fake"], "text": ["claim"], "subject": ["news"]}).to_csv(
        tmp_path / "Fake.csv", index=False
    )
    (tmp_path / "dataset_provenance.json").write_text(
        '{"source_label_mapping": {"0": "real", "1": "fake"}, '
        '"training_label_mapping": {"0": "real", "1": "fake"}}'
    )

    with pytest.raises(ValueError, match="label mapping"):
        load_isot_dataset(tmp_path)


def test_training_data_retains_verified_provenance(tmp_path: Path):
    pd.DataFrame({"title": ["real"], "text": ["report"], "subject": ["news"]}).to_csv(
        tmp_path / "True.csv", index=False
    )
    pd.DataFrame({"title": ["fake"], "text": ["claim"], "subject": ["news"]}).to_csv(
        tmp_path / "Fake.csv", index=False
    )
    (tmp_path / "dataset_provenance.json").write_text(
        '{"dataset": "GonzaloA/fake_news", '
        '"source_label_mapping": {"0": "fake", "1": "real"}, '
        '"training_label_mapping": {"0": "real", "1": "fake"}}'
    )

    dataset = load_isot_dataset(tmp_path)

    assert dataset.attrs["dataset_provenance"]["dataset"] == "GonzaloA/fake_news"


def test_liar_loader_keeps_the_requested_split_held_out(tmp_path: Path):
    row = "id\ttrue\tverified statement\tsubject\tspeaker\tjob\tstate\tparty\t0\t0\t0\t0\t0\tcontext\n"
    (tmp_path / "train.tsv").write_text(row)
    (tmp_path / "test.tsv").write_text(row.replace("true", "false", 1))

    dataset = load_liar_dataset(tmp_path, splits=("test.tsv",))

    assert dataset["label"].tolist() == [1]
