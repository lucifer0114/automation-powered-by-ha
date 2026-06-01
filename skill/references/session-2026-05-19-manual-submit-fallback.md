# Session note: manual submit fallback when the helper misses the composer

Observed on several 黄河新闻网 video posts:

- The persistent Playwright profile could load the post body and comments normally.
- The automation helper sometimes printed: `未自动找到“评论”按钮，直接尝试定位评论输入框。仍未找到评论输入框。`
- A direct DOM probe still found a visible textarea:
  - selector: `textarea[placeholder="发布你的评论"]`
  - visibility: `true`
- The comment could then be submitted reliably by:
  1. clicking the textarea
  2. filling the comment text
  3. clicking `button:has-text("评论")` with `force=True`
- After submit, verify via `body.innerText` that the comment appears in the time-sorted list before generating the proof screenshot.

Useful verification pattern:

- check `await page.locator('textarea').count()`
- inspect placeholder / visibility / bounding box
- use `body.innerText` rather than relying only on locator text hits when confirming the new comment

This is a fallback for the same class of Weibo pages where the helper's composer search is brittle, especially video posts with overlay players and modal controls.