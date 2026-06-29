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

    def evaluate(self, js, arg=None):
        return self.box


class FakePage:
    def __init__(self, box):
        self.box = box

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
        return self.box


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
