from app.config import Settings


def test_loads_fact_check_key_from_project_local_secret_file(tmp_path, monkeypatch):
    secret_dir = tmp_path / ".local-secrets"
    secret_dir.mkdir()
    (secret_dir / "truthlens.env").write_text("FACT_CHECK_API_KEY=local-test-key\n")
    monkeypatch.chdir(tmp_path)

    assert Settings().FACT_CHECK_API_KEY == "local-test-key"
