# Session 2026-05-19: Direct DOM composer fallback for stubborn Weibo posts

This session exposed a reusable recovery pattern for Weibo posts where the helper fails to see the composer even though the page is otherwise correct.

## What happened

- On some video-heavy posts, `weibo_manual_comment_flow.py --submit --like` reported:
  - `未自动找到“评论”按钮，直接尝试定位评论输入框。`
  - `仍未找到评论输入框。`
- A fresh Playwright probe still showed:
  - the post body matched the requested URL
  - one visible textarea with placeholder `发布你的评论`
  - a visible `评论` button near the composer
- The submit button could carry a `disabled` class / `disabled` attribute in the DOM but still be clickable with `force=True`.

## Reliable recovery path

1. Open the target post in the persistent profile.
2. Verify the visible body text matches the requested post.
3. Probe the live DOM for:
   - `textarea[placeholder="发布你的评论"]`
   - `button:has-text("评论")`
4. If the helper cannot find the composer, bypass it and fill the textarea directly.
5. Submit with `click(force=True)` on the visible `评论` button; if that fails, use an Enter-key fallback.
6. Verify the result with `--capture-only --headless`, not only with a body-text reload.

## Verification lesson

- `body.innerText` immediately after submission is useful, but not always the final proof on these pages.
- The `--capture-only` path is the stronger confirmation because it switches to `按时间` and searches the live rendered comment tree.
- When `--capture-only` finds the comment, prefer the contextual boxed screenshot as the deliverable.

## Practical takeaway

For stubborn posts, treat the script helper as a convenience layer, not the source of truth. Live DOM inspection plus direct textarea interaction is the durable fallback.
