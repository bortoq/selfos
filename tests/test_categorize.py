from plugins.categorize_plugin import suggest_category


def test_suggest_work():
    assert suggest_category("Team standup meeting") == "Work"
    assert suggest_category("Client sync call") == "Work"


def test_suggest_health():
    assert suggest_category("Morning gym session") == "Health"
    assert suggest_category("Doctor appointment") == "Health"


def test_suggest_finance():
    assert suggest_category("Pay monthly invoice") == "Finance"
    assert suggest_category("Salary received") == "Finance"


def test_suggest_personal():
    assert suggest_category("Family dinner") == "Personal"
    assert suggest_category("Friend birthday") == "Personal"


def test_suggest_other():
    assert suggest_category("Random task") == "Other"
    assert suggest_category("Some random activity") == "Other"