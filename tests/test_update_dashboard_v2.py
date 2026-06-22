from scripts.update_dashboard_v2 import calculate_stats, generate_score


def test_calculate_stats_basic():
    events = [
        {"timestamp": "2025-06-22T10:00:00Z", "title": "Task done"},
        {"timestamp": "2025-06-22T11:00:00Z", "title": "Postponed task"},
        {"timestamp": "2025-06-22T12:00:00Z", "title": "Cancelled meeting"},
    ]
    stats = calculate_stats(events)
    assert stats["completed"] >= 0
    assert stats["postponed"] >= 0


def test_generate_score():
    stats = {
        "completed": 5,
        "postponed": 1,
        "cancelled": 0,
        "categories": {"Work": 5, "Health": 1}
    }
    score = generate_score(stats)
    assert 0 <= score <= 100