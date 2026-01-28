from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

def test_get_status():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["message"] == "LLM Council API is online"

@patch('council.get_gemini_response')
def test_ask_question(mock_gemini):
    mock_gemini.return_value = "Mocked response from Gemini"
    
    response = client.post("/ask", json={"question": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mocked response from Gemini"
    mock_gemini.assert_called_once_with("What is 2+2?")
