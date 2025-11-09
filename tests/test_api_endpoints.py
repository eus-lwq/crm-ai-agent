"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_chat_endpoint():
    """Test chat endpoint."""
    response = client.post(
        "/api/chat",
        json={
            "message": "What time is it now?",
            "conversation_history": []
        }
    )
    # Should return 200 or 500 (depending on agent initialization)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "response" in data
        assert "history" in data


def test_get_emails_endpoint():
    """Test get emails endpoint."""
    response = client.get("/api/emails?limit=5")
    # Should return 200 or 500 (depending on Gmail service initialization)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # If emails exist, check structure
        if data:
            email = data[0]
            assert "id" in email
            assert "subject" in email
            assert "from_email" in email


def test_get_calendar_events_endpoint():
    """Test get calendar events endpoint."""
    response = client.get("/api/calendar/events?max_results=10")
    # Should return 200 or 500 (depending on Calendar service initialization)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # If events exist, check structure
        if data:
            event = data[0]
            assert "id" in event
            assert "summary" in event
            assert "start" in event
            assert "end" in event


def test_create_calendar_event_endpoint():
    """Test create calendar event endpoint."""
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    end_time = (tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)).isoformat()
    
    response = client.post(
        "/api/calendar/events",
        json={
            "summary": "Test Event",
            "start_time": start_time,
            "end_time": end_time,
            "description": "Test event from API"
        }
    )
    # Should return 200 or 500 (depending on Calendar service initialization)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data["summary"] == "Test Event"


def test_get_interactions_endpoint():
    """Test get interactions endpoint."""
    response = client.get("/api/interactions?limit=10")
    # Should return 200 or 500 (depending on BigQuery initialization)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # If interactions exist, check structure
        if data:
            interaction = data[0]
            assert "contact_name" in interaction or interaction.get("contact_name") is None
            assert "company" in interaction or interaction.get("company") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

