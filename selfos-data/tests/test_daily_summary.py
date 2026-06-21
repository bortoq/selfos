from scripts.daily_summary import generate_summary


def test_generate_summary_empty():
    assert generate_summary([]) == "No activity recorded today."


def test_generate_summary_basic():
    events = [
        {"type": "commit", "title": "Fix bug"},
        {"type": "event", "title": "Team meeting"},
        {"type": "commit", "title": "Add tests"},
    ]
    result = generate_summary(events)
    assert "3 events" in result
    assert "Commits: 2" in result
    assert "Meetings: 1" in result


def test_generate_summary_categories():
    events = [
        {"type": "commit", "title": "Work task", "metadata": {"category": "Work"}},
        {"type": "event", "title": "Gym", "metadata": {"category": "Health"}},
    ]
    result = generate_summary(events)
    assert "Work(1)" in result or "Health(1)" in result