from pathlib import Path

import pandas as pd
import pytest

from ml.scripts import download_data


def test_huggingface_label_contract_maps_one_to_real_and_zero_to_fake():
    records = pd.DataFrame({"label": [0, 1], "title": ["fake", "real"]})

    real, fake = download_data.split_labelled_articles(records)

    assert real["title"].tolist() == ["real"]
    assert fake["title"].tolist() == ["fake"]


def test_legacy_csv_cache_without_provenance_is_rejected(tmp_path: Path):
    (tmp_path / "True.csv").write_text("title,text\nreal,text\n")
    (tmp_path / "Fake.csv").write_text("title,text\nfake,text\n")

    with pytest.raises(ValueError, match="dataset_provenance.json"):
        download_data.require_dataset_provenance(tmp_path)


def test_provenance_requires_the_verified_source_mapping(tmp_path: Path):
    (tmp_path / "dataset_provenance.json").write_text(
        '{"source_label_mapping": {"0": "real", "1": "fake"}}'
    )

    with pytest.raises(ValueError, match="label mapping"):
        download_data.require_dataset_provenance(tmp_path)
