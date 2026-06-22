import pytest
from plugins.weekly_report_plugin import WeeklyReportPlugin


def test_weekly_report_plugin():
    plugin = WeeklyReportPlugin()
    result = plugin.execute(events=[{"type": "commit"}, {"type": "event"}])
    assert result["total_events"] == 2
    assert result["commits"] == 1