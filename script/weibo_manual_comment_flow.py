#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw


OUTPUT_DIR = Path.home() / "outputs/weibo-comment-shots"
PROFILE_DIR = Path.home() / ".playwright-weibo-profile"


def configure_wslg_env():
    """Make headed Chromium work reliably when launched from non-interactive WSL shells."""
    if not os.environ.get("DISPLAY") and Path("/tmp/.X11-unix/X0").exists():
        os.environ["DISPLAY"] = ":0"
    if not os.environ.get("XDG_RUNTIME_DIR") and Path("/mnt/wslg/runtime-dir").exists():
        os.environ["XDG_RUNTIME_DIR"] = "/mnt/wslg/runtime-dir"
    if not os.environ.get("WAYLAND_DISPLAY") and Path("/mnt/wslg/runtime-dir/wayland-0").exists():
        os.environ["WAYLAND_DISPLAY"] = "wayland-0"
    if not os.environ.get("PULSE_SERVER") and Path("/mnt/wslg/PulseServer").exists():
        os.environ["PULSE_SERVER"] = "unix:/mnt/wslg/PulseServer"


def safe_stem(text: str, limit: int = 48) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", text).strip("_")
    return (cleaned or "comment")[:limit]


def find_comment_locator(page, comment_text: str):
    candidates = [
        f'text={comment_text}',
        f'blockquote:has-text("{comment_text}")',
        f'div:has-text("{comment_text}")',
        f'span:has-text("{comment_text}")',
        f'p:has-text("{comment_text}")',
    ]
    for selector in candidates:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0 and locator.is_visible(timeout=1500):
                return locator, selector
        except Exception:
            continue
    return None, None


def draw_red_box(raw_path: Path, boxed_path: Path, box: dict):
    image = Image.open(raw_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    x0 = max(int(box["x"]) - 8, 0)
    y0 = max(int(box["y"]) - 8, 0)
    x1 = min(int(box["x"] + box["width"]) + 8, image.width - 1)
    y1 = min(int(box["y"] + box["height"]) + 8, image.height - 1)
    for offset in range(4):
        draw.rectangle([x0 - offset, y0 - offset, x1 + offset, y1 + offset], outline=(255, 0, 0), width=2)
    image.save(boxed_path)


def locator_document_box(locator, expand_selector: str | None = None):
    js = """
    (el, { expandSelector }) => {
        let target = el;
        if (expandSelector) {
            const expanded = target.closest(expandSelector);
            if (expanded) target = expanded;
        }
        const r = target.getBoundingClientRect();
        return {
            x: r.x + window.scrollX,
            y: r.y + window.scrollY,
            width: r.width,
            height: r.height,
            right: r.right + window.scrollX,
            bottom: r.bottom + window.scrollY,
        };
    }
    """
    return locator.evaluate(js, {"expandSelector": expand_selector})


def first_visible_document_box(page, selectors: list[str]):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=2000)
            return locator_document_box(locator), selector
        except Exception:
            continue
    return None, None


def save_contextual_crop(full_raw_path: Path, focused_raw_path: Path, focused_boxed_path: Path, crop_box: dict, highlight_box: dict):
    image = Image.open(full_raw_path).convert("RGB")
    left = max(int(crop_box["x"]), 0)
    top = max(int(crop_box["y"]), 0)
    right = min(int(crop_box["right"]), image.width)
    bottom = min(int(crop_box["bottom"]), image.height)
    cropped = image.crop((left, top, right, bottom))
    cropped.save(focused_raw_path)

    relative_box = {
        "x": highlight_box["x"] - left,
        "y": highlight_box["y"] - top,
        "width": highlight_box["width"],
        "height": highlight_box["height"],
    }
    draw = ImageDraw.Draw(cropped)
    x0 = max(int(relative_box["x"]) - 8, 0)
    y0 = max(int(relative_box["y"]) - 8, 0)
    x1 = min(int(relative_box["x"] + relative_box["width"]) + 8, cropped.width - 1)
    y1 = min(int(relative_box["y"] + relative_box["height"]) + 8, cropped.height - 1)
    for offset in range(4):
        draw.rectangle([x0 - offset, y0 - offset, x1 + offset, y1 + offset], outline=(255, 0, 0), width=2)
    cropped.save(focused_boxed_path)


def fill_comment_box(page, comment_text: str):
    selectors = [
        'textarea',
        '[contenteditable="true"]',
        'div[role="textbox"]',
        'div[contenteditable="plaintext-only"]',
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=3000)
            locator.click(timeout=2000)
            try:
                locator.fill(comment_text, timeout=2000)
            except Exception:
                locator.press("Control+A", timeout=1000)
                locator.type(comment_text, delay=30, timeout=5000)
            return locator, selector
        except Exception:
            continue
    return None, None


def click_comment_button(page):
    selectors = [
        'button:has-text("评论")',
        '[role="button"]:has-text("评论")',
        'a:has-text("评论")',
        'span:has-text("评论")',
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=3000)
            locator.click(timeout=3000)
            return selector
        except Exception:
            continue
    return None


def ensure_post_liked(page):
    selectors = [
        'article button[title="赞"]',
        'article .woo-like-main',
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=3000)
            state = locator.evaluate(
                """
                el => ({
                    className: el.className || '',
                    countClass: el.querySelector('.woo-like-count')?.className || '',
                    title: el.getAttribute('title') || '',
                    text: (el.innerText || el.textContent || '').trim(),
                })
                """
            )
            if 'woo-like-liked' in (state.get('countClass') or '') or 'liked' in (state.get('className') or ''):
                return 'already-liked', selector, state
            locator.click(timeout=3000)
            page.wait_for_timeout(1500)
            after = locator.evaluate(
                """
                el => ({
                    className: el.className || '',
                    countClass: el.querySelector('.woo-like-count')?.className || '',
                    title: el.getAttribute('title') || '',
                    text: (el.innerText || el.textContent || '').trim(),
                })
                """
            )
            if 'woo-like-liked' in (after.get('countClass') or '') or 'liked' in (after.get('className') or ''):
                return 'liked-now', selector, after
            return 'clicked-unknown', selector, after
        except Exception:
            continue
    return None, None, None


def main():
    parser = argparse.ArgumentParser(description="Manual-assisted Weibo comment screenshot workflow")
    parser.add_argument("--url", required=True, help="Target Weibo URL")
    parser.add_argument("--comment", required=True, help="Comment text to locate and box")
    parser.add_argument("--headless", action="store_true", help="Run headless (not recommended for manual login)")
    parser.add_argument("--submit", action="store_true", help="Try to auto-fill and auto-submit the comment")
    parser.add_argument("--like", action="store_true", help="Ensure the target Weibo post is liked before capture/submission")
    parser.add_argument("--capture-only", action="store_true", help="Skip submission and just locate an existing matching comment for screenshot evidence")
    parser.add_argument("--full-page-primary", action="store_true", help="Use full-page boxed screenshot as the primary output instead of the focused contextual crop")
    args = parser.parse_args()

    configure_wslg_env()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    stem = safe_stem(args.comment)
    raw_path = OUTPUT_DIR / f"{stem}_raw.png"
    boxed_path = OUTPUT_DIR / f"{stem}_boxed.png"
    focused_raw_path = OUTPUT_DIR / f"{stem}_context_raw.png"
    focused_boxed_path = OUTPUT_DIR / f"{stem}_context_boxed.png"

    print("[0/5] GUI env:", {
        "DISPLAY": os.environ.get("DISPLAY"),
        "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"),
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR"),
    }, flush=True)
    print("[1/5] Launching Chromium with persistent profile...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=args.headless,
            viewport={"width": 1440, "height": 1800},
        )
        page = browser.new_page()
        page.set_default_timeout(15000)

        print(f"[2/5] Opening: {args.url}", flush=True)
        page.goto(args.url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass

        if args.like:
            print("[2.5/5] Ensuring the post is liked...", flush=True)
            like_status, like_selector, like_state = ensure_post_liked(page)
            if like_status is None:
                print("未自动找到点赞按钮。", flush=True)
            else:
                print(f"LIKE_STATUS={like_status}", flush=True)
                print(f"LIKE_SELECTOR={like_selector}", flush=True)
                print(f"LIKE_STATE={like_state}", flush=True)

        if args.submit:
            print("[3/5] Trying to auto-fill and auto-submit the comment...", flush=True)
            button_selector = click_comment_button(page)
            if button_selector:
                print(f"已先点击评论按钮，按钮选择器: {button_selector}", flush=True)
                page.wait_for_timeout(1500)
            else:
                print("未自动找到“评论”按钮，直接尝试定位评论输入框。", flush=True)

            box_locator, box_selector = fill_comment_box(page, args.comment)
            if box_locator is None and button_selector is not None:
                page.wait_for_timeout(1500)
                box_locator, box_selector = fill_comment_box(page, args.comment)
            if box_locator is None:
                print("仍未找到评论输入框。", flush=True)
                browser.close()
                sys.exit(4)
            print(f"已填入评论，输入框选择器: {box_selector}", flush=True)

            submit_selector = click_comment_button(page)
            if not submit_selector:
                print("未自动找到可提交的“评论”按钮。", flush=True)
                browser.close()
                sys.exit(5)
            print(f"已点击评论按钮，按钮选择器: {submit_selector}", flush=True)
            try:
                page.wait_for_load_state("networkidle", timeout=6000)
            except PlaywrightTimeoutError:
                pass
        elif args.capture_only:
            print("[3/5] Capture-only mode: skipping comment submission and locating existing comment only...", flush=True)
        else:
            print("\n请在打开的浏览器里手动完成以下动作：", flush=True)
            print("  1) 登录微博", flush=True)
            print("  2) 如需点赞请手动点赞", flush=True)
            print(f"  3) 手动发布这条评论：{args.comment}", flush=True)
            input("\n完成后回到当前终端，按 Enter 继续截图与标注... ")

        print("[4/5] Trying to locate your comment on the page...", flush=True)
        page.bring_to_front()
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        try:
            page.get_by_text("按时间").first.click(timeout=5000)
            page.wait_for_timeout(2000)
            print("已切换评论排序到：按时间", flush=True)
        except Exception:
            print("未能切换到“按时间”，将按当前排序继续查找。", flush=True)

        locator, selector = find_comment_locator(page, args.comment)
        if locator is None:
            print("未能直接定位到评论文本。正在截全页原图，供后续人工检查。", flush=True)
            page.screenshot(path=str(raw_path), full_page=True)
            print(f"RAW_SCREENSHOT={raw_path.resolve()}", flush=True)
            print("BOXED_SCREENSHOT=NOT_FOUND", flush=True)
            browser.close()
            sys.exit(2)

        print(f"找到评论，使用选择器: {selector}", flush=True)
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass

        text_box = locator_document_box(locator)
        highlight_box = locator_document_box(locator, '.item1, .wbpro-list, .woo-box-flex.item1in, .con1, .text')
        if not text_box:
            print("评论已找到，但无法读取其坐标。仅输出原始截图。", flush=True)
            page.screenshot(path=str(raw_path), full_page=True)
            print(f"RAW_SCREENSHOT={raw_path.resolve()}", flush=True)
            print("BOXED_SCREENSHOT=NOT_FOUND", flush=True)
            browser.close()
            sys.exit(3)

        article_box, article_selector = first_visible_document_box(page, ['article', '.wbpro-feed-content'])
        if not article_box:
            article_box = {
                'x': max(highlight_box['x'] - 40, 0),
                'y': max(highlight_box['y'] - 500, 0),
                'right': highlight_box['right'] + 40,
                'bottom': highlight_box['bottom'] + 80,
            }
            article_selector = 'fallback'

        crop_box = {
            'x': max(min(article_box['x'], highlight_box['x']) - 20, 0),
            'y': max(article_box['y'] - 20, 0),
            'right': max(article_box['right'], highlight_box['right']) + 20,
            'bottom': highlight_box['bottom'] + 80,
        }

        print("[5/5] Saving full-page screenshot...", flush=True)
        page.screenshot(path=str(raw_path), full_page=True)

        print("[5/5+] Drawing red rectangle around the detected comment...", flush=True)
        draw_red_box(raw_path, boxed_path, text_box)
        save_contextual_crop(raw_path, focused_raw_path, focused_boxed_path, crop_box, highlight_box)

        primary_raw_path = raw_path if args.full_page_primary else focused_raw_path
        primary_boxed_path = boxed_path if args.full_page_primary else focused_boxed_path
        primary_mode = "full_page" if args.full_page_primary else "contextual"

        print(f"POST_SELECTOR={article_selector}", flush=True)
        print(f"PRIMARY_MODE={primary_mode}", flush=True)
        print(f"RAW_SCREENSHOT={primary_raw_path.resolve()}", flush=True)
        print(f"BOXED_SCREENSHOT={primary_boxed_path.resolve()}", flush=True)
        print(f"FULL_RAW_SCREENSHOT={raw_path.resolve()}", flush=True)
        print(f"FULL_BOXED_SCREENSHOT={boxed_path.resolve()}", flush=True)
        print(f"CONTEXT_RAW_SCREENSHOT={focused_raw_path.resolve()}", flush=True)
        print(f"CONTEXT_BOXED_SCREENSHOT={focused_boxed_path.resolve()}", flush=True)
        print("[5/5++] Closing page/context while preserving login state in the persistent profile...", flush=True)
        page.close()
        browser.close()


if __name__ == "__main__":
    main()
