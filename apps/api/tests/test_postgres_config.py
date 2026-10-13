from sqlalchemy.engine import make_url

from adapters.postgres.config import database_url


def test_url_preserves_credentials_with_url_and_ini_special_characters(monkeypatch) -> None:
    settings = {
        "POSTGRES_HOST": "postgres", "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "qh", "POSTGRES_USER": "owner@local",
        "POSTGRES_PASSWORD": "test-only:@/%?#value",
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    url = database_url()
    decoded = make_url(url.render_as_string(hide_password=False))
    assert decoded.username == settings["POSTGRES_USER"]
    assert decoded.password == settings["POSTGRES_PASSWORD"]
    assert decoded.host == "postgres" and decoded.port == 5432
    assert decoded.database == "qh" and decoded.drivername == "postgresql+psycopg"
    assert settings["POSTGRES_PASSWORD"] not in str(url)
