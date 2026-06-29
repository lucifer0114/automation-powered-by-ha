import importlib.util
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "script" / "weibo_manual_comment_flow.py"
spec = importlib.util.spec_from_file_location("weibo_flow", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
weibo_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weibo_flow)


class FakeLocator:
    def __init__(self, count=1, visible=True):
        self._count = count
        self.visible = visible
        self.wait_calls = []

    @property
    def first(self):
        return self

    def count(self):
        return self._count

    def wait_for(self, state=None, timeout=None):
        self.wait_calls.append((state, timeout))
        if self._count == 0 or not self.visible:
            raise RuntimeError("not visible")


class FakePage:
    def __init__(self, fail_networkidle=False, selectors=None):
        self.fail_networkidle = fail_networkidle
        self.selectors = selectors or {}
        self.wait_calls = []

    def wait_for_load_state(self, state, timeout=None):
        self.wait_calls.append((state, timeout))
        if self.fail_networkidle:
            raise PlaywrightTimeoutError("timeout")

    def locator(self, selector):
        return self.selectors.get(selector, FakeLocator(count=0, visible=False))


def test_wait_for_page_ready_returns_networkidle_when_available():
    page = FakePage()
    assert weibo_flow.wait_for_page_ready(page) == "networkidle"
    assert page.wait_calls[0][0] == "networkidle"


def test_wait_for_page_ready_falls_back_to_first_visible_selector():
    page = FakePage(
        fail_networkidle=True,
        selectors={"article": FakeLocator(count=1, visible=True)},
    )
    assert weibo_flow.wait_for_page_ready(page) == "selector:article"


def test_wait_for_page_ready_returns_timeout_fallback_when_nothing_visible():
    page = FakePage(fail_networkidle=True)
    assert weibo_flow.wait_for_page_ready(page) == "timeout-fallback"
