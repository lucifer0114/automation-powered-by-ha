# Session note: direct textarea + force-submit fallback on visible composer

Date: 2026-06-02

## What happened
- On post `https://weibo.com/2105171747/QFrH6E0UO`, `locator('textarea[placeholder="发布你的评论"]').wait_for(state="visible")` timed out in one run even though the live page already had a usable visible composer.
- A probe immediately after showed:
  - `textarea` count = 1
  - the textarea was visible
  - the textarea had a real bounding box
  - the submit button `button:has-text("评论")` was visible
- `get_by_text("评论").first.click()` targeted a disabled-looking text/span path and timed out, but the actual submit button still worked when clicked with `force=True` after filling the textarea.

## Reliable recovery pattern
1. Verify the page body matches the requested post before typing.
2. If the placeholder-specific textarea locator stalls, probe generic `textarea` directly.
3. If generic `textarea` is visible and has a bounding box, use it instead of spending more time on the helper path.
4. Fill the comment, then target the actual `button:has-text("评论")` element.
5. If the button still carries a `disabled` class but the composer is filled, try `click(force=True)`.
6. Verify success from the `comments/create` response plus the new visible comment item, ideally after switching to `按时间`.

## Why this matters
- Some pages expose a real usable composer while the more specific placeholder/label path remains brittle.
- The visible `评论` text node is not always the same thing as the real clickable submit button.
- A `disabled` CSS class on the submit control is not enough to conclude the post cannot be submitted.
