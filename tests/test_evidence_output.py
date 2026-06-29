import importlib.util
from pathlib import Path

from PIL import Image

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "script" / "weibo_manual_comment_flow.py"
spec = importlib.util.spec_from_file_location("weibo_flow", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
weibo_flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weibo_flow)


class FakeLocator:
    def __init__(self, box):
        self.box = box
        self.scroll_calls = []

    def evaluate(self, js, arg=None):
        return self.box

    def scroll_into_view_if_needed(self, timeout=None):
        self.scroll_calls.append(timeout)


class FakePage:
    def __init__(self, box, viewport=None):
        self.box = box
        self.viewport = viewport or {"scrollX": 0, "scrollY": 0, "innerWidth": 500, "innerHeight": 500}
        self.screenshots = []

    def locator(self, selector):
        return self

    @property
    def first(self):
        return self

    def count(self):
        return 1

    def wait_for(self, state=None, timeout=None):
        return None

    def evaluate(self, js, arg=None):
        if isinstance(arg, dict) and "highlightTop" in arg:
            return None
        if "innerWidth" in js and "innerHeight" in js:
            return self.viewport
        return self.box

    def screenshot(self, **kwargs):
        self.screenshots.append(kwargs)
        target = Path(kwargs["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        width = kwargs.get("clip", {}).get("width", 400)
        height = kwargs.get("clip", {}).get("height", 300)
        Image.new("RGB", (width, height), "white").save(target)


def test_safe_stem_normalizes_and_truncates_text():
    value = weibo_flow.safe_stem("这 是 / 一条? 很长很长很长的评论!!!", limit=10)
    assert value == "这_是_一条_很长很"


def test_locator_document_box_returns_locator_box():
    box = {"x": 10, "y": 20, "width": 30, "height": 40, "right": 40, "bottom": 60}
    locator = FakeLocator(box)
    assert weibo_flow.locator_document_box(locator) == box


def test_first_visible_document_box_returns_first_matching_selector():
    box = {"x": 1, "y": 2, "width": 300, "height": 200, "right": 301, "bottom": 202}
    page = FakePage(box)
    found_box, selector = weibo_flow.first_visible_document_box(page, ["article", ".wbpro-feed-content"])
    assert found_box == box
    assert selector == "article"


def test_build_timings_payload_fills_missing_keys_with_numbers():
    payload = weibo_flow.build_timings_payload({"open_url_ms": 120, "locate_comment_ms": 340}, total_ms=999)
    assert payload["open_url_ms"] == 120
    assert payload["locate_comment_ms"] == 340
    assert payload["total_ms"] == 999
    assert isinstance(payload["submit_wait_ms"], (int, float))
    assert isinstance(payload["capture_artifacts_ms"], (int, float))


def test_can_use_viewport_context_capture_requires_crop_inside_viewport():
    page = FakePage({"x": 0, "y": 0, "width": 1, "height": 1, "right": 1, "bottom": 1})
    inside = {"x": 10, "y": 15, "right": 210, "bottom": 215}
    outside = {"x": 10, "y": 15, "right": 610, "bottom": 615}

    assert weibo_flow.can_use_viewport_context_capture(page, inside) is True
    assert weibo_flow.can_use_viewport_context_capture(page, outside) is False


def test_capture_comment_artifacts_uses_viewport_fast_path_when_crop_fits(monkeypatch, tmp_path):
    locator = FakeLocator({"x": 120, "y": 140, "width": 80, "height": 30, "right": 200, "bottom": 170})
    page = FakePage(locator.box)
    raw = tmp_path / "raw.png"
    boxed = tmp_path / "boxed.png"
    focus_raw = tmp_path / "focus_raw.png"
    focus_boxed = tmp_path / "focus_boxed.png"
    calls = []

    monkeypatch.setattr(weibo_flow, "find_post_body_box", lambda _p, _h: {"box": {"x": 90, "y": 40, "right": 260, "bottom": 180}, "selector": "article"})
    monkeypatch.setattr(weibo_flow, "first_visible_document_box", lambda _p, _s: ({"x": 90, "y": 40, "right": 260, "bottom": 180}, "article"))
    monkeypatch.setattr(weibo_flow, "hide_overlay_chrome", lambda _p: None)
    monkeypatch.setattr(weibo_flow, "draw_red_box", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("draw_red_box should not run in viewport fast path")))
    monkeypatch.setattr(weibo_flow, "save_contextual_crop", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("save_contextual_crop should not run in viewport fast path")))

    def fake_save_clipped(page_obj, focused_raw_path, focused_boxed_path, crop_box, highlight_box):
        calls.append((crop_box, highlight_box))
        Image.new("RGB", (220, 170), "white").save(focused_raw_path)
        Image.new("RGB", (220, 170), "white").save(focused_boxed_path)

    monkeypatch.setattr(weibo_flow, "save_clipped_contextual_screenshot", fake_save_clipped)

    exit_code = weibo_flow.capture_comment_artifacts(page, locator, 'dom-comment-wrapper', 'article', raw, boxed, focus_raw, focus_boxed)

    assert exit_code == 0
    assert len(calls) == 1
    assert not raw.exists()
    assert focus_raw.exists()
    assert focus_boxed.exists()


def test_compute_context_crop_box_includes_header_shell_and_interaction_row():
    framing_box = {"x": 360, "y": 50, "right": 980, "bottom": 760}
    article_box = {"x": 368, "y": 215, "right": 972, "bottom": 676}
    highlight_box = {"x": 414, "y": 980, "width": 556, "height": 45, "right": 970, "bottom": 1025}

    crop = weibo_flow.compute_context_crop_box(framing_box, article_box, highlight_box)

    assert crop["y"] <= 40
    assert crop["bottom"] == highlight_box["bottom"] + weibo_flow.CONTEXT_CROP_BOTTOM_PADDING
    assert crop["x"] <= framing_box["x"]
    assert crop["right"] >= framing_box["right"]


def test_draw_red_box_and_save_contextual_crop_create_output_files(tmp_path):
    raw = tmp_path / "raw.png"
    boxed = tmp_path / "boxed.png"
    focus_raw = tmp_path / "focus_raw.png"
    focus_boxed = tmp_path / "focus_boxed.png"
    Image.new("RGB", (400, 300), "white").save(raw)

    highlight = {"x": 120, "y": 140, "width": 80, "height": 30, "right": 200, "bottom": 170}
    crop = {"x": 40, "y": 60, "right": 260, "bottom": 230}

    weibo_flow.draw_red_box(raw, boxed, highlight)
    weibo_flow.save_contextual_crop(raw, focus_raw, focus_boxed, crop, highlight)

    assert boxed.exists()
    assert focus_raw.exists()
    assert focus_boxed.exists()
    assert Image.open(focus_raw).size == (220, 170)
