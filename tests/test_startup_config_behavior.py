import pytest


def test_create_app_fails_fast_when_database_url_is_missing(monkeypatch):
    import studypdf.app_factory as app_factory
    import studypdf.db as db_module

    monkeypatch.setattr(db_module, "STUDYPDF_DATABASE_URL", "")
    monkeypatch.setattr(app_factory, "start_processing_worker", lambda _app: None)

    with pytest.raises(RuntimeError, match="STUDYPDF_DATABASE_URL"):
        app_factory.create_app()


def test_database_target_log_does_not_include_password(monkeypatch, caplog):
    import studypdf.app_factory as app_factory
    import studypdf.db as db_module

    monkeypatch.setattr(
        db_module,
        "STUDYPDF_DATABASE_URL",
        "postgresql://postgres:secret-password@db.example.supabase.co:5432/postgres?sslmode=require",
    )
    monkeypatch.setattr(app_factory, "check_database_connection", lambda: None)
    monkeypatch.setattr(app_factory, "start_processing_worker", lambda _app: None)

    with caplog.at_level("INFO"):
        app_factory.create_app()

    assert "db.example.supabase.co:5432/postgres" in caplog.text
    assert "secret-password" not in caplog.text


def test_connect_db_uses_configured_timeout(monkeypatch):
    import studypdf.db as db_module

    calls = []

    class FakeConnection:
        pass

    def fake_connect(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeConnection()

    monkeypatch.setattr(db_module, "STUDYPDF_DATABASE_URL", "postgresql://postgres:pass@db.example/postgres")
    monkeypatch.setattr(db_module, "STUDYPDF_DATABASE_CONNECT_TIMEOUT_SECONDS", 7)
    monkeypatch.setattr(db_module, "connect", fake_connect)

    db_module.connect_db()

    assert calls[0][1]["connect_timeout"] == 7
