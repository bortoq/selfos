from selfos.browser import BrowserService


def test_browser_add_and_get_link():
    browser = BrowserService()
    browser.add_link("selfos", "https://github.com/bortoq/selfos", "development")
    assert browser.get_link("selfos").url == "https://github.com/bortoq/selfos"


def test_browser_list_links():
    browser = BrowserService()
    links = browser.list_links("productivity")
    assert len(links) >= 3  # gmail, calendar, notion, todoist


def test_browser_open_link():
    browser = BrowserService()
    url = browser.open_link("github")
    assert "github.com" in url