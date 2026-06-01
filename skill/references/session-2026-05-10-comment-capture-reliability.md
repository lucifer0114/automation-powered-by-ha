# Session note: Weibo comment capture reliability

This session reinforced a few reliable patterns for Weibo proof screenshots:

## What worked
- On pages like `https://weibo.com/2606218210/QEsqWrUA6` and `https://weibo.com/7850154169/QEpZx01rs`, the post could be liked and the comment could be submitted from the visible textarea even when the `评论` button path was flaky in automation.
- After submission, `body.innerText` was the most dependable way to confirm the comment existed.
- Switching the comment list to `按时间` helped surface the fresh comment near the top of the list.
- For proof, a cropped contextual screenshot with the comment row highlighted was better than a full-page shot.

## What was flaky
- The script's `capture-only` path often returned `BOXED_SCREENSHOT=NOT_FOUND` even when the comment was actually present.
- Raw DOM searches for the exact comment string sometimes missed the item, while `body.innerText` still contained it.
- Very large full-page screenshots were harder to verify visually than a tight crop around the comment region.

## Practical workaround
1. Submit the comment.
2. Verify in `body.innerText`.
3. Switch to `按时间`.
4. If automated text matching fails, use a manual crop around the visible comment row and add a red box.
5. Prefer screenshots where the author name and timestamp are still visible.

## Note
This session showed that the composer may already be visible; do not assume the textarea is hidden until `评论` is clicked.