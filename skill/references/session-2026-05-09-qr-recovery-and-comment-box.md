# Session note: QR recovery + comment box fallback

Date: 2026-05-09

## What happened
- Opening a Weibo URL often landed on `Sina Visitor System` or a QR login card.
- `browser_snapshot()` sometimes returned `(empty page)` even when the page was actually recoverable.
- `browser_vision()` was more reliable for determining whether the QR login card was visible or whether the page had already returned to the post.
- After a QR scan / login transition, the page could still be stale or mismatched, so the safest next step was to re-open the target URL and confirm the post text with `browser_console`.

## Reliable recovery pattern
1. Re-open the requested Weibo URL.
2. If the page shows the QR login card, return a visible QR screenshot to the user.
3. After scan/login, re-open the same URL again instead of assuming the state has advanced.
4. Use `browser_console` to extract the visible post text and verify the author/hashtags match the requested link.
5. If the headless composer fails to find the textarea, click the visible `评论` button first, then fill `textarea`, then submit.

## Pitfalls
- QR refresh controls may not be present; re-navigation is a better refresh than hunting for a hidden reload icon.
- A stale snapshot can look empty while the live page already contains the target post.
- A successful comment submit can still require a second pass to locate and box the comment for evidence.
- Do not trust the URL alone when the browser context looks stale; verify the post body before acting.

## Evidence outputs used
- `*_context_boxed.png` is the primary handoff artifact.
- `*_raw.png` and `*_boxed.png` may exist for debugging.
