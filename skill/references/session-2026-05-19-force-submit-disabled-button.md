# Session note: Weibo comment submit via force-click

Observed on `https://weibo.com/2105171747/QFUnG1yn1` with persistent profile `~/.playwright-weibo-profile`.

Key finding:
- The comment composer existed as `textarea[placeholder="发布你的评论"]`.
- After filling the textarea, the visible `评论` button still had a `disabled` class in the DOM.
- Despite that, `button:has-text("评论")` could be clicked with `force=True`, and the comment was submitted successfully.

Working sequence:
1. Scroll to the post/comments area.
2. Fill the textarea.
3. If needed, use a real typing path once, but `fill()` was sufficient here.
4. Force-click the visible `评论` button.
5. Wait briefly and verify the new comment appears in the comment list under the current account.
6. Switch to `按时间` before capture.
7. Capture contextual boxed evidence.

Verification note:
- After force-click submission, `body.innerText` contained the new comment and the contextual screenshot showed the comment in the thread.

Pitfall:
- Do not treat the `disabled` class on the `评论` button as proof that submission is impossible.
