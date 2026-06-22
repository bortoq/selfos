from __future__ import annotations

from selfos.llm.models import Suggestion
from selfos.llm.state import SuggestionStateStore


def test_state_store_saves_suggestion_and_rating(tmp_path) -> None:
    store = SuggestionStateStore(base_dir=tmp_path)
    suggestion = Suggestion(
        id="s1",
        title="Review inbox",
        summary="There are unread emails",
        action="email_reply",
        confidence=0.8,
        backend_used="llm",
        source_context={"gmail": True},
        status="new",
    )
    store.save_suggestions([suggestion])
    store.rate("s1", 4)

    saved = store.list_suggestions()
    ratings = store.load_ratings()
    assert saved[0]["id"] == "s1"
    assert ratings["s1"] == 4
