import importlib.util
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "script" / "weibo_manual_comment_flow.py"
spec = importlib.util.spec_from_file_location("weibo_flow", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
weibo_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weibo_flow)


class FakeLocator:
    def __init__(self, name, count=1, visible=True):
        self.name = name
        self._count = count
        self.visible = visible
        self.waited = []

    @property
    def first(self):
        return self

    def count(self):
        return self._count

    def wait_for(self, state=None, timeout=None):
        self.waited.append((state, timeout))
        if self._count == 0 or not self.visible:
            raise RuntimeError(f"{self.name} not visible")

    def is_visible(self, timeout=None):
        return self._count > 0 and self.visible


class FakePage:
    def __init__(self, fail_networkidle=False, selectors=None):
        self.fail_networkidle = fail_networkidle
        self.selectors = selectors or {}
        self.wait_load_calls = []
        self.wait_timeout_calls = []

    def wait_for_load_state(self, state, timeout=None):
        self.wait_load_calls.append((state, timeout))
        if state == "networkidle" and self.fail_networkidle:
            raise PlaywrightTimeoutError("networkidle timeout")
        return None

    def wait_for_timeout(self, ms):
        self.wait_timeout_calls.append(ms)

    def locator(self, selector):
        return self.selectors.get(selector, FakeLocator(selector, count=0, visible=False))


def test_wait_for_page_ready_returns_networkidle_when_available():
    page = FakePage(fail_networkidle=False)

    result = weibo_flow.wait_for_page_ready(page, context="initial-load")

    assert result == "networkidle"
    assert page.wait_load_calls[0][0] == "networkidle"


def test_wait_for_page_ready_falls_back_to_known_selectors_when_networkidle_times_out():
    page = FakePage(
        fail_networkidle=True,
        selectors={
            '[data-testid="comment-list"]': FakeLocator('comment-list', count=1, visible=True),
        },
    )

    result = weibo_flow.wait_for_page_ready(
        page,
        context="after-submit",
        readiness_selectors=['[data-testid="comment-list"]'],
    )

    assert result == 'selector:[data-testid="comment-list"]'
    assert page.wait_load_calls[0][0] == 'networkidle'


def test_wait_for_page_ready_uses_timeout_sleep_when_no_signal_available():
    page = FakePage(fail_networkidle=True)

    result = weibo_flow.wait_for_page_ready(page, context="fallback", fallback_wait_ms=900)

    assert result == 'timeout-fallback'
    assert page.wait_timeout_calls == [900]
