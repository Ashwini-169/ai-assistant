import time

from fastapi.testclient import TestClient

from services import tts_service


def _fake_post(url, json, timeout):  # pylint: disable=redefined-outer-name
    class _DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

    return _DummyResponse()


def test_speak(monkeypatch):
    monkeypatch.setattr(tts_service._http_session, "post", _fake_post)

    with TestClient(tts_service.app) as client:
        start = time.perf_counter()
        response = client.post("/speak", json={"text": "Hello world"})
        latency = time.perf_counter() - start

    print(f"tts latency: {latency:.3f}s")
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True
    assert data["backend_status"] == 200
