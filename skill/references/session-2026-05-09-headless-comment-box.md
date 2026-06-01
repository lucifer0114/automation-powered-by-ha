# Session note: headless Weibo comment box pitfall

Observed during a real run on 2026-05-09:
- Opening a Weibo post directly in headless mode can show the post, the visible `评论` button, and the composer area in a partially loaded state.
- The comment `textarea` may not be usable until the page first clicks the visible `评论` button.
- A flow that tries `fill_comment_box()` before clicking `评论` can fail with `未自动找到评论输入框` even though the comment UI exists.
- Pausing for manual recovery via `input()` is unsafe in non-interactive shells: it raises `EOFError`.

Reliable sequence for automation:
1. Open the post.
2. Ensure the post is liked.
3. Click the visible `评论` button first.
4. Wait briefly for the composer to expand.
5. Fill the textarea.
6. Click `评论` again to submit.
7. Switch to `按时间` if needed and locate the posted comment for evidence.

Practical takeaway:
- Prefer an automatic retry path after clicking `评论` over any interactive `input()` pause.
- If the first fill attempt fails, click `评论`, wait ~1–2 seconds, and retry the textarea locator before giving up.