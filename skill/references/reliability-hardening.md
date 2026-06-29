# Reliability hardening for Weibo comment evidence

Use this when the Playwright flow can produce false positives or mis-boxed screenshots.

## P0 guardrails

1. Split **open comment panel** from **submit comment**.
   - Do not reuse the same selector routine for both actions.
   - Prefer separate helpers such as `open_comment_panel()` and `submit_comment()`.
   - Submit should prefer explicit send/publish controls (`发送`, `发布`) over generic `评论` entry buttons.

2. Treat submission as successful only after **comment re-detection**.
   - After clicking submit, re-check whether the exact comment text appears inside the comment area.
   - If the page falls back to login / risk-control state, treat submission as failed.
   - If re-detection fails, stop before generating boxed evidence screenshots.

3. Scope comment lookup to the **comment list/container**, not the entire page.
   - Whole-page text search can match repost text, article body, or unrelated comments.
   - First locate the comment root, then search for the target text within that root.

4. Add explicit **login / risk-control detection** at multiple checkpoints.
   - Check immediately after page load.
   - Check after submit.
   - Check again before final screenshot/cropping.

## Next-tier reliability improvements

1. Narrow composer selectors.
   - Prefer composer-scoped selectors like `[data-testid="comment-composer"] ...` before generic `contenteditable` nodes.
   - Generic editable nodes can target unrelated editors on the page.

2. Verify the `按时间` sort switch.
   - Do not assume success after click.
   - Confirm an active/selected state selector for the `按时间` tab or control.

3. Harden liked-state detection.
   - Check multiple signals: class name, count class, title text such as `已赞` / `取消赞`, and visible label text.

4. Normalize highlight/crop boxes.
   - Prefer expanded comment-card boxes when available.
   - Fall back to the text box when expanded geometry is missing.
   - Clamp crop coordinates to non-negative bounds and ensure `right > x`, `bottom > y`.

5. Replace brittle `networkidle` waits with layered readiness checks.
   - Treat `networkidle` as an optimistic fast path, not the only success criterion.
   - After timeout, fall back to concrete DOM signals: main post visible, comment root present, composer visible, or other workflow-specific selectors.
   - Keep a short final timeout fallback so long-polling / streaming Weibo pages do not deadlock the flow.
   - Centralize this in a helper such as `wait_for_page_ready()` so page-open, post-submit, and pre-crop waits use the same policy.

## Regression-test targets

Keep lightweight tests for these behaviors:
- login-state detection
- comment search scoped to comments root
- open-panel vs submit-button separation
- submit success requires visible comment match
- composer selector priority
- time-sort verification
- crop-box normalization
