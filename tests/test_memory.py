from memory import memory_manager


class _FakeStore:
    def __init__(self) -> None:
        self.items = []

    def upsert(self, payload_id, embedding, content):  # pylint: disable=unused-argument
        self.items.append(content)

    def search(self, embedding, top_k=3):  # pylint: disable=unused-argument
        return [(self.items[0], 0.9)] if self.items else []


def test_memory_retrieval(monkeypatch):
    monkeypatch.setattr(memory_manager, "embed", lambda text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(memory_manager, "VectorStore", lambda dim: _FakeStore())

    manager = memory_manager.MemoryManager()
    manager.add_interaction("user likes pizza", "assistant suggests toppings")
    manager.add_interaction("user asks about weather", "assistant gives forecast")

    results = manager.retrieve("pizza")
    formatted = manager.format_memories(results)

    assert results
    assert formatted
