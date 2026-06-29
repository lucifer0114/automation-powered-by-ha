import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "script" / "weibo_manual_comment_flow.py"
spec = importlib.util.spec_from_file_location("weibo_flow", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
weibo_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weibo_flow)


class FakeLocator:
    def __init__(self, name, count=1, visible=True, fill_raises=False, eval_results=None):
        self.name = name
        self._count = count
        self.visible = visible
        self.fill_raises = fill_raises
        self.eval_results = list(eval_results or [])
        self.clicked = 0
        self.filled = []
        self.pressed = []
        self.typed = []
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

    def click(self, timeout=None, force=False):
        self.clicked += 1

    def fill(self, text, timeout=None):
        if self.fill_raises:
            raise RuntimeError("fill failed")
        self.filled.append(text)

    def press(self, key, timeout=None):
        self.pressed.append(key)

    def type(self, text, delay=None, timeout=None):
        self.typed.append(text)

    def evaluate(self, js, arg=None):
        if self.eval_results:
            return self.eval_results.pop(0)
        return None


class FakePage:
    def __init__(self, selectors=None):
        self.selectors = selectors or {}
        self.waits = []
        self.eval_map = {}

    def locator(self, selector):
        return self.selectors.get(selector, FakeLocator(selector, count=0, visible=False))

    def wait_for_timeout(self, ms):
        self.waits.append(ms)

    def evaluate(self, js, arg=None):
        if js in self.eval_map:
            value = self.eval_map[js]
            return value(arg) if callable(value) else value
        raise RuntimeError(f"unexpected evaluate: {js[:40]}")


def test_fill_comment_box_uses_visible_textarea_first():
    textarea = FakeLocator("textarea")
    page = FakePage({
        'textarea[placeholder="发布你的评论"]': textarea,
    })

    locator, selector = weibo_flow.fill_comment_box(page, "测试评论")

    assert locator is textarea
    assert selector == 'textarea[placeholder="发布你的评论"]'
    assert textarea.filled == ["测试评论"]
    assert textarea.clicked == 1


def test_fill_comment_box_falls_back_to_type_when_fill_fails():
    textarea = FakeLocator("textarea", fill_raises=True)
    page = FakePage({
        'textarea[placeholder="发布你的评论"]': textarea,
    })

    locator, selector = weibo_flow.fill_comment_box(page, "测试评论")

    assert locator is textarea
    assert selector == 'textarea[placeholder="发布你的评论"]'
    assert textarea.pressed == ["Control+A"]
    assert textarea.typed == ["测试评论"]


def test_ensure_post_liked_detects_already_liked_state():
    like = FakeLocator(
        "like",
        eval_results=[{"className": "", "countClass": "woo-like-count woo-like-liked", "title": "赞", "text": "4.6万"}],
    )
    page = FakePage({'article button[title="赞"]': like})

    status, selector, state = weibo_flow.ensure_post_liked(page)

    assert status == "already-liked"
    assert selector == 'article button[title="赞"]'
    assert state["countClass"].endswith("woo-like-liked")
    assert like.clicked == 0


def test_ensure_post_liked_clicks_and_returns_liked_now():
    like = FakeLocator(
        "like",
        eval_results=[
            {"className": "", "countClass": "woo-like-count", "title": "赞", "text": "88"},
            {"className": "_cur liked", "countClass": "woo-like-count woo-like-liked", "title": "赞", "text": "89"},
        ],
    )
    page = FakePage({'article button[title="赞"]': like})

    status, selector, state = weibo_flow.ensure_post_liked(page)

    assert status == "liked-now"
    assert selector == 'article button[title="赞"]'
    assert state["countClass"].endswith("woo-like-liked")
    assert like.clicked == 1
    assert page.waits == [700]


def test_fill_comment_box_uses_dom_probe_fallback_when_standard_locators_false_negative():
    page = FakePage({
        'textarea[placeholder="发布你的评论"]': FakeLocator("placeholder", count=1, visible=False),
        'textarea': FakeLocator("generic", count=0, visible=False),
        '[contenteditable="true"]': FakeLocator("editable", count=0, visible=False),
        'div[role="textbox"]': FakeLocator("textbox", count=0, visible=False),
        'div[contenteditable="plaintext-only"]': FakeLocator("plaintext", count=0, visible=False),
    })
    direct = FakeLocator("direct-dom")
    page.selectors['textarea[data-hermes-direct-composer="1"]'] = direct
    page.eval_map[weibo_flow.DOM_COMPOSER_PROBE_JS] = True

    locator, selector = weibo_flow.fill_comment_box(page, "测试评论")

    assert locator is direct
    assert selector == 'textarea[data-hermes-direct-composer="1"]'
    assert direct.filled == ["测试评论"]
