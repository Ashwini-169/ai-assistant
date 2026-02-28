from humanization.emotion_engine import EmotionEngine


def test_emotion_update():
    engine = EmotionEngine()
    state = engine.update("I love this")
    assert state.user_sentiment == "positive"
    assert state.conversation_depth == 1
    context = engine.emotional_context()
    assert "sentiment" in context
