import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "script" / "weibo_manual_comment_flow.py"
spec = importlib.util.spec_from_file_location("weibo_flow", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
weibo_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weibo_flow)


class FakeBody:
    def __init__(self, texts):
        self.texts = list(texts)

    def inner_text(self, timeout=None):
        if self.texts:
            return self.texts.pop(0)
        return ""


class FakeVisible:
    @property
    def first(self):
        return self

    def wait_for(self, state=None, timeout=None):
        return None


class FakeButton:
    def __init__(self):
        self.clicked = 0

    @property
    def first(self):
        return self

    def click(self, timeout=None, force=False):
        self.clicked += 1


class FakeMouse:
    def __init__(self):
        self.wheels = []

    def wheel(self, x, y):
        self.wheels.append((x, y))


class FakePage:
    def __init__(self, body_texts):
        self.body = FakeBody(body_texts)
        self.mouse = FakeMouse()
        self.sort_button = FakeButton()
        self.waits = []
        self.load_calls = []

    def wait_for_timeout(self, ms):
        self.waits.append(ms)

    def wait_for_load_state(self, state, timeout=None):
        self.load_calls.append((state, timeout))

    def locator(self, selector):
        if selector == 'body':
            return self.body
        if selector == '.wbpro-list, .item1, .vue-recycle-scroller__item-view':
            return FakeVisible()
        return FakeVisible()

    def get_by_text(self, text):
        assert text == '按时间'
        return self.sort_button


def test_wait_for_time_sort_refresh_returns_true_when_comment_appears():
    page = FakePage(["still loading", "目标评论 已出现"])
    assert weibo_flow.wait_for_time_sort_refresh(page, "目标评论") is True
    assert page.waits[:2] == [350, 800]


def test_wait_for_time_sort_refresh_returns_false_when_comment_never_appears():
    page = FakePage(["a", "b", "c"])
    assert weibo_flow.wait_for_time_sort_refresh(page, "目标评论") is False
    assert page.waits == [350, 800, 1400]


def test_locate_comment_returns_direct_match(monkeypatch):
    page = FakePage([])
    target = object()

    def fake_find(_page, text):
        return target, "dom-comment-wrapper"

    monkeypatch.setattr(weibo_flow, "find_comment_locator", fake_find)

    locator, selector, phase = weibo_flow.locate_comment(page, "目标评论")
    assert locator is target
    assert selector == "dom-comment-wrapper"
    assert phase == "direct"


def test_locate_comment_switches_to_time_sort_when_direct_match_misses(monkeypatch):
    page = FakePage([])
    target = object()
    calls = []

    def fake_find(_page, text):
        calls.append(text)
        if len(calls) == 1:
            return None, None
        return target, ".item1 [structured 0]"

    monkeypatch.setattr(weibo_flow, "find_comment_locator", fake_find)
    monkeypatch.setattr(weibo_flow, "wait_for_time_sort_refresh", lambda _p, _t=None: True)

    locator, selector, phase = weibo_flow.locate_comment(page, "目标评论")

    assert locator is target
    assert selector == ".item1 [structured 0]"
    assert phase == "after-time-sort"
    assert page.sort_button.clicked == 1
    assert page.mouse.wheels[0] == (0, -1200)
