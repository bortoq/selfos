from scripts.create_task import create_task_event


def test_create_task_event_structure():
    event = create_task_event("Finish documentation", "Self OS", 1)

    assert event["type"] == "task"
    assert event["title"] == "Finish documentation"
    assert event["metadata"]["project"] == "Self OS"
    assert event["metadata"]["priority"] == 1
    assert event["metadata"]["created_via"] == "selfos"
    assert "timestamp" in event
    assert "id" in event