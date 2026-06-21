from scripts.quick_note import suggest_tags_and_category


def test_suggest_work_meeting():
    result = suggest_tags_and_category("Had a team sync meeting today")
    assert "meeting" in result["suggested_tags"]
    assert result["suggested_category"] == "Work"


def test_suggest_shopping():
    result = suggest_tags_and_category("Need to buy milk and bread")
    assert "shopping" in result["suggested_tags"]
    assert result["suggested_category"] == "Personal"


def test_suggest_health():
    result = suggest_tags_and_category("Went to the gym and doctor")
    assert "health" in result["suggested_tags"]
    assert result["suggested_category"] == "Health"


def test_suggest_idea():
    result = suggest_tags_and_category("Remember this idea for later")
    assert "idea" in result["suggested_tags"]


def test_suggest_default():
    result = suggest_tags_and_category("Just a random thought")
    assert result["suggested_category"] == "Other"
    # Функция возвращает ["idea"] для слова "thought"
    assert len(result["suggested_tags"]) > 0