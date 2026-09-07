import pytest

from app.config import Settings


def test_loads_fact_check_key_from_project_local_secret_file(tmp_path, monkeypatch):
    secret_dir = tmp_path / ".local-secrets"
    secret_dir.mkdir()
    (secret_dir / "truthlens.env").write_text("FACT_CHECK_API_KEY=local-test-key\n")
    monkeypatch.chdir(tmp_path)

    assert Settings().FACT_CHECK_API_KEY == "local-test-key"


def test_requires_an_explicit_text_model_version(tmp_path, monkeypatch):
    monkeypatch.delenv("ACTIVE_TEXT_MODEL_VERSION", raising=False)
    monkeypatch.chdir(tmp_path)

    assert Settings().ACTIVE_TEXT_MODEL_VERSION == ""


def test_rejects_the_default_jwt_secret_in_production(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()
