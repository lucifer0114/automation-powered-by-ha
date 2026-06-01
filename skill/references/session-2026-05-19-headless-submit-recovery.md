# Session note: headless submit recovery on Weibo composer

Observed on Weibo posts from `weibo.com/2105171747/*` in the current persistent profile:
- `textarea[placeholder="发布你的评论"]` can exist but still be hard to interact with until the comment area is fully expanded.
- Clicking the visible `评论` control in the comment section can reveal the composer when a plain locator wait stalls.
- After filling the textarea, the submit button may still carry a `disabled` class visually, but `click(force=True)` on the button text `评论` succeeded in posting the comment.
- Successful verification came from re-reading `body.innerText` and confirming the freshly posted comment text appears under `按时间`.

Practical recovery order:
1. scroll to the post/comment section
2. if needed, click `评论` to expand the composer
3. fill `textarea[placeholder="发布你的评论"]`
4. submit with `button:has-text("评论")` using `force=True` if needed
5. switch to `按时间` and verify the new comment text in the DOM/body text
