import pytest

from scripts import download_models


def test_skips_download_when_no_active_model_version_is_configured(monkeypatch):
    monkeypatch.setattr(download_models, "HF_MODEL_REPO", "owner/models")
    monkeypatch.setattr(download_models, "MODEL_VERSION", "")
    monkeypatch.setattr(
        download_models,
        "models_already_present",
        lambda _version: pytest.fail("must not inspect an unspecified model"),
    )

    with pytest.raises(SystemExit) as result:
        download_models.main()

    assert result.value.code == 0
