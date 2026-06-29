#!/usr/bin/env python3
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw


OUTPUT_DIR = Path.home() / "outputs/weibo-comment-shots"
PROFILE_DIR = Path.home() / ".playwright-weibo-profile"

# Preferred contextual evidence composition for Weibo proof shots:
# 1) posting account header (e.g. "黄河新闻网")
# 2) post body
# 3) interaction/status row (转发 / 评论 / 点赞 counts)
# 4) relevant comment thread with the boxed target comment
#
# These margins are intentionally tuned so the crop stays tight while still preserving
# those four proof layers in one frame when the page layout allows it.
CONTEXT_CROP_SIDE_PADDING = 8
CONTEXT_CROP_TOP_PADDING = 18
CONTEXT_CROP_BOTTOM_PADDING = 44
FALLBACK_ARTICLE_SIDE_PADDING = 40
FALLBACK_ARTICLE_LOOKBACK = 500
FALLBACK_ARTICLE_BOTTOM_PADDING = 80


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
    now = datetime.now()
    date_tokens = [
        f"{now.year % 100}-{now.month}-{now.day}",
        f"{now.year % 100}-{now.month:02d}-{now.day:02d}",
        f"{now.year}-{now.month}-{now.day}",
        f"{now.year}-{now.month:02d}-{now.day:02d}",
    ]

    try:
        matched = page.evaluate(
            """
            ({ commentText, dateTokens }) => {
                document.querySelectorAll('[data-hermes-target-comment="1"]').forEach(el => {
                    el.removeAttribute('data-hermes-target-comment');
                });
                const commentRootSelectors = [
                    '.wbpro-list',
                    '.CommentList',
                    '[class*="comment"] [class*="list"]',
                    '[class*="Comment"] [class*="List"]',
                ];
                const cardSelectors = [
                    '.item1',
                    '.wbpro-scroller-item',
                    '.vue-recycle-scroller__item-view',
                    '.woo-box-flex.item1in.item1in',
                    '.woo-box-item-flex.con1',
                    '.item1in',
                    '.con1',
                    '.text',
                ];
                const roots = commentRootSelectors
                    .flatMap(sel => Array.from(document.querySelectorAll(sel)))
                    .filter((el, idx, arr) => arr.indexOf(el) === idx);
                const visibleRoots = roots.filter(el => {
                    const r = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return r.width > 100 && r.height > 40 && style.visibility !== 'hidden' && style.display !== 'none';
                });
                const searchScopes = visibleRoots.length ? visibleRoots : [document.body];
                let best = null;
                for (const scope of searchScopes) {
                    const nodes = cardSelectors
                        .flatMap(sel => Array.from(scope.querySelectorAll(sel)))
                        .filter((el, idx, arr) => arr.indexOf(el) === idx);
                    for (const el of nodes) {
                        const text = (el.innerText || '').trim();
                        if (!text || !text.includes(commentText)) continue;
                        if (el.matches('textarea, [contenteditable="true"], [role="textbox"]')) continue;
                        let target = el;
                        const wrapper = el.closest('.item1, .wbpro-scroller-item, .vue-recycle-scroller__item-view, .woo-box-flex.item1in.item1in, .woo-box-item-flex.con1, .item1in, .con1');
                        if (wrapper) {
                            const wrapperText = (wrapper.innerText || '').trim();
                            if (wrapperText.includes(commentText)) target = wrapper;
                        }
                        const r = target.getBoundingClientRect();
                        if (r.width <= 80 || r.height <= 20 || r.height > 420) continue;
                        const style = window.getComputedStyle(target);
                        if (style.visibility === 'hidden' || style.display === 'none') continue;
                        if (r.bottom < 0 || r.top > window.innerHeight + 4000) continue;
                        const targetText = (target.innerText || '').trim();
                        const hasToday = dateTokens.some(token => targetText.includes(token));
                        const textLines = targetText.split('\n').map(line => line.trim()).filter(Boolean);
                        const hasAuthorLikeHeader = textLines.some(line => line.length >= 1 && line.length <= 24)
                            || !!target.querySelector('a, img, [class*="avatar"], [class*="name"]');
                        const exactCount = targetText.split(commentText).length - 1;
                        const rank = [
                            hasToday ? 0 : 1,
                            hasAuthorLikeHeader ? 0 : 1,
                            exactCount === 1 ? 0 : 1,
                            r.top + window.scrollY,
                            Math.abs(r.height - 72),
                            Math.abs(r.width - 520),
                            targetText.length,
                        ];
                        if (!best || rank.join('|') < best.rank.join('|')) {
                            best = { el: target, rank };
                        }
                    }
                }
                if (!best) return false;
                best.el.setAttribute('data-hermes-target-comment', '1');
                return true;
            }
            """,
            {"commentText": comment_text, "dateTokens": date_tokens},
        )
        if matched:
            locator = page.locator('[data-hermes-target-comment="1"]').first
            if locator.count() > 0 and locator.is_visible(timeout=500):
                return locator, 'dom-comment-wrapper'
    except Exception:
        pass

    structured_selectors = [
        '.item1',
        '.wbpro-scroller-item',
        '.vue-recycle-scroller__item-view',
        '.woo-box-flex.item1in.item1in',
        '.woo-box-item-flex.con1',
        '.item1in',
        '.con1',
    ]
    best_structured = None
    for selector in structured_selectors:
        group = page.locator(selector).filter(has_text=comment_text)
        try:
            total = min(group.count(), 8)
        except Exception:
            continue
        for i in range(total):
            locator = group.nth(i)
            try:
                if not locator.is_visible(timeout=500):
                    continue
                box = locator_document_box(locator)
                if not box or box.get('width', 0) <= 80 or box.get('height', 0) <= 20 or box.get('height', 0) > 420:
                    continue
                text = (locator.inner_text(timeout=500) or '').strip()
                has_today = any(token in text for token in date_tokens)
                exact_count = text.count(comment_text)
                rank = (
                    0 if has_today else 1,
                    0 if exact_count == 1 else 1,
                    box['y'],
                    abs(box['height'] - 72),
                    abs(box['width'] - 520),
                    len(text),
                )
                if best_structured is None or rank < best_structured[0]:
                    best_structured = (rank, locator, f"{selector} [structured {i}]")
            except Exception:
                continue
    if best_structured is not None:
        return best_structured[1], best_structured[2]

    candidates = [
        f'text={comment_text}',
        f'blockquote:has-text("{comment_text}")',
        f'div:has-text("{comment_text}")',
        f'span:has-text("{comment_text}")',
        f'p:has-text("{comment_text}")',
    ]
    for selector in candidates:
        group = page.locator(selector)
        try:
            total = min(group.count(), 8)
        except Exception:
            continue
        best = None
        for i in range(total):
            locator = group.nth(i)
            try:
                if not locator.is_visible(timeout=500):
                    continue
                box = locator.evaluate(
                    """
                    el => {
                        const r = el.getBoundingClientRect();
                        return {
                            x: r.x + window.scrollX,
                            y: r.y + window.scrollY,
                            width: r.width,
                            height: r.height,
                        };
                    }
                    """
                )
                if not box or box.get('width', 0) <= 0 or box.get('height', 0) <= 0:
                    continue
                rank = (box['y'], box['x'])
                if best is None or rank < best[0]:
                    best = (rank, locator, f"{selector} [match {i}]")
            except Exception:
                continue
        if best is not None:
            return best[1], best[2]
    return None, None


def wait_for_page_ready(page, timeout_ms: int = 4000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        return "networkidle"
    except PlaywrightTimeoutError:
        pass

    for selector in [
        'article',
        '.wbpro-feed-content',
        'textarea[placeholder="发布你的评论"]',
        'button:has-text("评论")',
    ]:
        locator = page.locator(selector).first
        try:
            if locator.count() == 0:
                continue
            locator.wait_for(state="visible", timeout=1200)
            return f"selector:{selector}"
        except Exception:
            continue
    return "timeout-fallback"


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


def hide_overlay_chrome(page):
    try:
        page.evaluate(
            """
            () => {
                document.querySelectorAll('[data-hermes-hidden-overlay="1"]').forEach(el => {
                    el.style.removeProperty('display');
                    el.style.removeProperty('visibility');
                    el.removeAttribute('data-hermes-hidden-overlay');
                });
                for (const el of document.querySelectorAll('*')) {
                    const cs = window.getComputedStyle(el);
                    if (!['fixed', 'sticky'].includes(cs.position)) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width < 100 || r.height < 24) continue;
                    if (r.left > window.innerWidth || r.top > window.innerHeight) continue;
                    el.setAttribute('data-hermes-hidden-overlay', '1');
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                }
            }
            """
        )
    except Exception:
        pass


def find_post_body_box(page, highlight_box: dict):
    try:
        return page.evaluate(
            """
            ({ highlightTop, highlightLeft, highlightRight }) => {
                const selectors = ['.wbpro-feed-content', 'article', '.woo-panel-main'];
                const candidates = selectors
                    .flatMap(sel => Array.from(document.querySelectorAll(sel)).map(el => ({ sel, el })))
                    .filter(({ el }, idx, arr) => arr.findIndex(item => item.el === el) === idx);
                let best = null;
                for (const { sel, el } of candidates) {
                    const r = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    if (style.visibility === 'hidden' || style.display === 'none') continue;
                    if (r.width < 240 || r.height < 120) continue;
                    const box = {
                        x: r.x + window.scrollX,
                        y: r.y + window.scrollY,
                        width: r.width,
                        height: r.height,
                        right: r.right + window.scrollX,
                        bottom: r.bottom + window.scrollY,
                    };
                    const text = (el.innerText || '').trim();
                    const looksLikePost = text.length > 40;
                    const aboveComment = box.y <= highlightTop;
                    const overlap = Math.max(0, Math.min(box.right, highlightRight) - Math.max(box.x, highlightLeft));
                    const overlapRatio = overlap / Math.max(1, Math.min(box.width, highlightRight - highlightLeft));
                    const sameColumn = overlapRatio > 0.45 || Math.abs(box.x - highlightLeft) < 80;
                    if (!sameColumn) continue;
                    const distance = aboveComment ? (highlightTop - box.y) : 100000 + (box.y - highlightTop);
                    const widthPenalty = box.width >= 520 ? 0 : 1000 + Math.abs(box.width - 520);
                    const selectorPenalty = sel === '.wbpro-feed-content' ? 0 : (sel === 'article' ? 1 : 2);
                    const rank = [aboveComment ? 0 : 1, selectorPenalty, widthPenalty, distance, Math.abs(box.x - highlightLeft), Math.abs(box.height - 520)];
                    if (looksLikePost && (!best || rank.join('|') < best.rank.join('|'))) {
                        best = { box, sel, rank };
                    }
                }
                return best ? { box: best.box, selector: best.sel } : null;
            }
            """,
            {
                "highlightTop": highlight_box["y"],
                "highlightLeft": highlight_box["x"],
                "highlightRight": highlight_box["right"],
            },
        )
    except Exception:
        return None


def wait_for_time_sort_refresh(page, comment_text: str | None = None):
    checkpoints = [350, 800, 1400]
    for delay in checkpoints:
        page.wait_for_timeout(delay)
        try:
            page.wait_for_load_state("networkidle", timeout=1200)
        except Exception:
            pass
        try:
            page.locator('.wbpro-list, .item1, .vue-recycle-scroller__item-view').first.wait_for(state="visible", timeout=1200)
        except Exception:
            pass
        if comment_text:
            try:
                body_text = page.locator('body').inner_text(timeout=1200)
                if comment_text in body_text:
                    return True
            except Exception:
                pass
    return False


def locate_comment(page, comment_text: str, allow_time_sort_retry: bool = True):
    locator, selector = find_comment_locator(page, comment_text)
    if locator is not None:
        return locator, selector, "direct"

    if allow_time_sort_retry:
        try:
            page.mouse.wheel(0, -1200)
            page.wait_for_timeout(200)
        except Exception:
            pass
        try:
            page.get_by_text("按时间").first.click(timeout=1500, force=True)
            wait_for_time_sort_refresh(page, comment_text)
            print("已切换评论排序到：按时间", flush=True)
        except Exception:
            print("未能切换到“按时间”，将按当前排序继续查找。", flush=True)
        locator, selector = find_comment_locator(page, comment_text)
        if locator is not None:
            return locator, selector, "after-time-sort"

    try:
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(300)
    except Exception:
        pass
    locator, selector = find_comment_locator(page, comment_text)
    if locator is not None:
        return locator, selector, "after-scroll"

    if allow_time_sort_retry:
        try:
            page.mouse.wheel(0, 700)
            page.wait_for_timeout(350)
        except Exception:
            pass
        locator, selector = find_comment_locator(page, comment_text)
        if locator is not None:
            return locator, selector, "after-time-sort-scroll"

    return None, None, None


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


def save_clipped_contextual_screenshot(page, focused_raw_path: Path, focused_boxed_path: Path, crop_box: dict, highlight_box: dict):
    left = max(int(crop_box["x"]), 0)
    top = max(int(crop_box["y"]), 0)
    right = max(int(crop_box["right"]), left + 1)
    bottom = max(int(crop_box["bottom"]), top + 1)
    clip_box = {
        "x": left,
        "y": top,
        "width": max(right - left, 1),
        "height": max(bottom - top, 1),
    }
    page.screenshot(path=str(focused_raw_path), clip=clip_box)
    cropped = Image.open(focused_raw_path).convert("RGB")
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


def capture_comment_artifacts(page, locator, matched_selector: str, article_fallback_selector: str, raw_path: Path, boxed_path: Path, focused_raw_path: Path, focused_boxed_path: Path, full_page_primary: bool = False):
    try:
        locator.scroll_into_view_if_needed(timeout=2500)
    except Exception:
        pass

    text_box = locator_document_box(locator)
    if matched_selector == 'dom-comment-wrapper' or '[wrapper ' in matched_selector or '[structured ' in matched_selector:
        highlight_box = text_box
    else:
        highlight_box = locator_document_box(locator, '.item1, .wbpro-scroller-item, .vue-recycle-scroller__item-view, .woo-box-flex.item1in.item1in, .woo-box-item-flex.con1, .item1in, .con1, .text')
    if not text_box:
        print("评论已找到，但无法读取其坐标。仅输出原始截图。", flush=True)
        page.screenshot(path=str(raw_path), full_page=True)
        print(f"RAW_SCREENSHOT={raw_path.resolve()}", flush=True)
        print("BOXED_SCREENSHOT=NOT_FOUND", flush=True)
        return 3

    post_box_result = find_post_body_box(page, highlight_box)
    if post_box_result:
        article_box = post_box_result['box']
        article_selector = post_box_result['selector']
    else:
        article_box, article_selector = first_visible_document_box(page, ['article', '.wbpro-feed-content', '.woo-panel-main'])

    shell_box = None
    try:
        article_candidate, _ = first_visible_document_box(page, ['article'])
        if article_candidate and abs(article_candidate['x'] - highlight_box['x']) < 120:
            shell_box = article_candidate
    except Exception:
        shell_box = None

    if not article_box:
        article_box = shell_box or {
            'x': max(highlight_box['x'] - FALLBACK_ARTICLE_SIDE_PADDING, 0),
            'y': max(highlight_box['y'] - FALLBACK_ARTICLE_LOOKBACK, 0),
            'right': highlight_box['right'] + FALLBACK_ARTICLE_SIDE_PADDING,
            'bottom': highlight_box['bottom'] + FALLBACK_ARTICLE_BOTTOM_PADDING,
        }
        article_selector = article_fallback_selector

    framing_box = shell_box or article_box
    # Keep the contextual proof crop anchored to the whole post card, not just the
    # comment box. This helps preserve the account header and the interaction/status
    # row above the boxed target comment, which the user treats as part of the proof.
    crop_top = min(framing_box['y'], article_box['y'], highlight_box['y'])
    crop_box = {
        'x': max(min(framing_box['x'], article_box['x'], highlight_box['x']) - CONTEXT_CROP_SIDE_PADDING, 0),
        'y': max(crop_top - CONTEXT_CROP_TOP_PADDING, 0),
        'right': max(framing_box['right'], article_box['right'], highlight_box['right']) + CONTEXT_CROP_SIDE_PADDING,
        'bottom': highlight_box['bottom'] + CONTEXT_CROP_BOTTOM_PADDING,
    }

    if full_page_primary:
        print("[5/5] Saving full-page screenshot...", flush=True)
        hide_overlay_chrome(page)
        page.screenshot(path=str(raw_path), full_page=True)

        print("[5/5+] Drawing red rectangle around the detected comment...", flush=True)
        draw_red_box(raw_path, boxed_path, text_box)
        save_contextual_crop(raw_path, focused_raw_path, focused_boxed_path, crop_box, highlight_box)

        primary_raw_path = raw_path.resolve()
        primary_boxed_path = boxed_path.resolve()
        full_raw_value = str(raw_path.resolve())
        full_boxed_value = str(boxed_path.resolve())
        context_raw_value = str(focused_raw_path.resolve())
        context_boxed_value = str(focused_boxed_path.resolve())
        primary_mode = "full_page"
    else:
        print("[5/5] Saving full-page base screenshot for tight contextual crop...", flush=True)
        hide_overlay_chrome(page)
        page.screenshot(path=str(raw_path), full_page=True)
        save_contextual_crop(raw_path, focused_raw_path, focused_boxed_path, crop_box, highlight_box)
        primary_raw_path = focused_raw_path.resolve()
        primary_boxed_path = focused_boxed_path.resolve()
        full_raw_value = str(raw_path.resolve())
        full_boxed_value = "NOT_CAPTURED"
        context_raw_value = str(focused_raw_path.resolve())
        context_boxed_value = str(focused_boxed_path.resolve())
        primary_mode = "contextual"

    print(f"POST_SELECTOR={article_selector}", flush=True)
    print(f"PRIMARY_MODE={primary_mode}", flush=True)
    print(f"RAW_SCREENSHOT={primary_raw_path}", flush=True)
    print(f"BOXED_SCREENSHOT={primary_boxed_path}", flush=True)
    print(f"FULL_RAW_SCREENSHOT={full_raw_value}", flush=True)
    print(f"FULL_BOXED_SCREENSHOT={full_boxed_value}", flush=True)
    print(f"CONTEXT_RAW_SCREENSHOT={context_raw_value}", flush=True)
    print(f"CONTEXT_BOXED_SCREENSHOT={context_boxed_value}", flush=True)
    return 0


def fill_comment_box(page, comment_text: str):
    selectors = [
        'textarea[placeholder="发布你的评论"]',
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
            locator.wait_for(state="visible", timeout=1200)
            locator.click(timeout=1500, force=True)
            try:
                locator.fill(comment_text, timeout=2000)
            except Exception:
                locator.press("Control+A", timeout=1000)
                locator.type(comment_text, delay=30, timeout=5000)
            return locator, selector
        except Exception:
            continue
    return None, None


def click_comment_button(page, force: bool = False):
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
            locator.wait_for(state="visible", timeout=1500)
            locator.click(timeout=2000, force=force)
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
            locator.click(timeout=2500)
            page.wait_for_timeout(700)
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
    parser.add_argument("--capture-first-submit-fallback", action="store_true", help="Try to capture an existing matching comment first; if not found, submit and capture in the same browser session")
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
        ready_state = wait_for_page_ready(page, timeout_ms=4000)
        print(f"PAGE_READY={ready_state}", flush=True)

        if args.like:
            print("[2.5/5] Ensuring the post is liked...", flush=True)
            like_status, like_selector, like_state = ensure_post_liked(page)
            if like_status is None:
                print("未自动找到点赞按钮。", flush=True)
            else:
                print(f"LIKE_STATUS={like_status}", flush=True)
                print(f"LIKE_SELECTOR={like_selector}", flush=True)
                print(f"LIKE_STATE={like_state}", flush=True)

        should_try_capture_first = args.capture_first_submit_fallback and args.submit
        if should_try_capture_first:
            print("[3/5] Fast path: trying to capture an existing matching comment before submitting...", flush=True)
            existing_locator, existing_selector, existing_phase = locate_comment(page, args.comment)
            if existing_locator is not None:
                print(f"已复用现有评论，定位阶段: {existing_phase}，选择器: {existing_selector}", flush=True)
                exit_code = capture_comment_artifacts(
                    page,
                    existing_locator,
                    existing_selector,
                    existing_phase or 'existing-comment-fast-path',
                    raw_path,
                    boxed_path,
                    focused_raw_path,
                    focused_boxed_path,
                    full_page_primary=args.full_page_primary,
                )
                print("[5/5++] Closing page/context while preserving login state in the persistent profile...", flush=True)
                page.close()
                browser.close()
                sys.exit(exit_code)
            print("未复用到现有评论，继续执行提交流程。", flush=True)

        if args.submit:
            print("[3/5] Trying to auto-fill and auto-submit the comment...", flush=True)
            box_locator, box_selector = fill_comment_box(page, args.comment)
            button_selector = None
            if box_locator is None:
                button_selector = click_comment_button(page, force=True)
                if button_selector:
                    print(f"已点击评论按钮以展开输入框，按钮选择器: {button_selector}", flush=True)
                    page.wait_for_timeout(500)
                else:
                    print("未自动找到“评论”按钮，直接尝试定位评论输入框。", flush=True)
                box_locator, box_selector = fill_comment_box(page, args.comment)
            if box_locator is None:
                print("仍未找到评论输入框。", flush=True)
                browser.close()
                sys.exit(4)
            print(f"已填入评论，输入框选择器: {box_selector}", flush=True)

            submit_selector = click_comment_button(page, force=True)
            if not submit_selector:
                print("未自动找到可提交的“评论”按钮。", flush=True)
                browser.close()
                sys.exit(5)
            print(f"已点击评论按钮，按钮选择器: {submit_selector}", flush=True)
            page.wait_for_timeout(1200)
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

        locator, selector, locate_phase = locate_comment(page, args.comment)
        if locator is None:
            print("未能直接定位到评论文本。正在截全页原图，供后续人工检查。", flush=True)
            page.screenshot(path=str(raw_path), full_page=True)
            print(f"RAW_SCREENSHOT={raw_path.resolve()}", flush=True)
            print("BOXED_SCREENSHOT=NOT_FOUND", flush=True)
            browser.close()
            sys.exit(2)

        print(f"找到评论，定位阶段: {locate_phase}，使用选择器: {selector}", flush=True)
        exit_code = capture_comment_artifacts(
            page,
            locator,
            selector,
            locate_phase or 'fallback',
            raw_path,
            boxed_path,
            focused_raw_path,
            focused_boxed_path,
            full_page_primary=args.full_page_primary,
        )
        print("[5/5++] Closing page/context while preserving login state in the persistent profile...", flush=True)
        page.close()
        browser.close()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
