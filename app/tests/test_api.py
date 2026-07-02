import pytest
from unittest.mock import patch

@pytest.mark.anyio
@patch("app.api.router.process_audio_pipeline.delay")  # Мокаем вызов Celery
async def test_upload_audio_endpoint(mock_delay, client):
    """Тестируем, что эндпоинт принимает файл и ставит задачу в очередь."""
    
    # Симулируем загрузку аудиофайла
    file_payload = {"file": ("test_audio.mp3", b"fake_audio_content", "audio/mpeg")}
    
    response = await client.post("/api/v1/analyze", files=file_payload)
    
    # Проверяем стандарты ответа (202 Accepted)
    assert response.status_code == 202
    
    response_data = response.json()
    assert "task_id" in response_data
    assert response_data["status"] == "QUEUED"
    
    # Проверяем, что Celery таска реально была вызвана ровно 1 раз
    mock_delay.assert_called_once()