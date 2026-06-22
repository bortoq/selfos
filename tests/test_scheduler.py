from src.selfos.scheduler import Scheduler


def test_add_task():
    scheduler = Scheduler()
    task = scheduler.add_task("Finish Phase 3", "2025-07-01", 1)
    assert task["type"] == "task"
    assert task["metadata"]["status"] == "pending"


def test_add_event():
    scheduler = Scheduler()
    event = scheduler.add_event("Team meeting", "2025-06-25T10:00:00Z", 45)
    assert event["type"] == "event"
    assert event["metadata"]["duration_minutes"] == 45


def test_list_tasks():
    scheduler = Scheduler()
    scheduler.add_task("Task 1")
    scheduler.add_task("Task 2")
    tasks = scheduler.list_tasks()
    assert len(tasks) == 2


def test_complete_task():
    scheduler = Scheduler()
    task = scheduler.add_task("Important task")
    success = scheduler.complete_task(task["id"])
    assert success is True
    assert scheduler.list_tasks(status="completed")[0]["metadata"]["status"] == "completed"