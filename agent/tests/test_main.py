import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app, zip_store

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_question():
    mock_state = {
        "messages": [], "context": {}, "search_results": {},
        "phase": "clarify", "next_question": "어떤 기술 스택을 쓰시나요?",
        "zip_bytes": None,
    }
    with patch("main.graph.ainvoke", new_callable=AsyncMock, return_value=mock_state):
        response = client.post("/chat", json={
            "thread_id": "test-123",
            "message": "프론트엔드 앱을 만들고 싶어요",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "question"
    assert "text" in data


def test_chat_returns_ready_when_zip_ready():
    mock_state = {
        "messages": [], "context": {}, "search_results": {},
        "phase": "build", "next_question": None,
        "zip_bytes": b"PK fake zip",
    }
    with patch("main.graph.ainvoke", new_callable=AsyncMock, return_value=mock_state):
        response = client.post("/chat", json={
            "thread_id": "test-456",
            "message": "React와 TypeScript를 씁니다",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "ready"


def test_download_returns_zip():
    zip_store["dl-thread-1"] = b"PK fake zip bytes"
    response = client.get("/download/dl-thread-1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"


def test_download_missing_thread_returns_404():
    response = client.get("/download/nonexistent-thread")
    assert response.status_code == 404
