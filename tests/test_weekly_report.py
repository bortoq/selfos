from scripts.weekly_report import generate_weekly_report


def test_weekly_report_empty():
    result = generate_weekly_report([])
    assert "No activity" in result


def test_weekly_report_basic():
    events = [
        {"timestamp": "2025-06-20T10:00:00Z", "type": "commit", "title": "Fix bug"},
        {"timestamp": "2025-06-21T14:00:00Z", "type": "event", "title": "Meeting"},
        {"timestamp": "2025-06-22T09:00:00Z", "type": "commit", "title": "Add tests"},
    ]
    result = generate_weekly_report(events)
    assert len(result) > 50  # Просто проверяем, что отчёт не пустой


def test_weekly_report_categories():
    # Добавляем обязательное поле type
    events = [
        {"timestamp": "2025-06-20T10:00:00Z", "type": "event", "metadata": {"category": "Work"}},
        {"timestamp": "2025-06-21T14:00:00Z", "type": "event", "metadata": {"category": "Health"}},
    ]
    result = generate_weekly_report(events)
    assert len(result) > 30