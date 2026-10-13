"""Live Compose smoke tests; run inside the backend container."""

import json
import os
from urllib.request import urlopen

from neo4j import GraphDatabase
import psycopg


def test_frontend_serves_vite_entry() -> None:
    with urlopen("http://frontend:5173/", timeout=10) as response:
        assert response.status == 200
        html = response.read().decode()
    assert 'id="root"' in html
    assert "/src/main.tsx" in html
    with urlopen("http://frontend:5173/src/main.tsx", timeout=10) as response:
        assert response.status == 200
        assert "react" in response.read().decode()


def test_live_backend_health() -> None:
    with urlopen("http://backend:8000/health", timeout=10) as response:
        assert response.status == 200
        assert json.load(response) == {"status": "ok", "service": "qh-api"}


def test_mcp_health_from_app_network() -> None:
    with urlopen("http://mcp:3001/health", timeout=10) as response:
        assert response.status == 200
        assert json.load(response) == {"status": "ok", "service": "qh-mcp-server"}


def test_postgres_authenticated_internal_connection() -> None:
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)


def test_neo4j_authenticated_internal_connection() -> None:
    with GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        connection_timeout=10,
    ) as driver:
        records, _, _ = driver.execute_query("RETURN 1 AS value")
        assert records[0]["value"] == 1
