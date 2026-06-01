# Session note: Weibo video-post comment recovery

Observed on multiple 黄河新闻网 video posts where the generic helper sometimes failed to auto-find the comment composer.

## Reliable recovery pattern
1. Open the post in the persistent Playwright profile.
2. Verify the visible正文 matches the requested URL before acting.
3. If the helper cannot find `评论` / the textarea, inspect the live DOM:
   - `textarea[placeholder="发布你的评论"]` may already exist and be visible.
   - A `button:has-text("评论")` submit button may exist even when the helper says it cannot find the composer.
4. Manually click the textarea, fill the comment, then force-click the visible `评论` button.
5. If the comment does not appear immediately in body text, re-open the page and verify after switching to `按时间`.
6. Use the capture-only pass to generate the boxed/contextual evidence screenshot once the comment is visible.

## Useful observations
- Video posts can expose the composer while a video player / modal-related UI is also present in the page tree.
- A failed helper pass does not necessarily mean the page is blocked; the textarea is often present and directly usable.
- For these posts, the comment often verifies cleanly only after a fresh reload or an explicit `按时间` sort in the capture-only pass.
