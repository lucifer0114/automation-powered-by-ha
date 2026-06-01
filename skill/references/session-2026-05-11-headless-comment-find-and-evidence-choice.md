# Session note: headless comment finding and evidence selection

Date: 2026-05-11

## What happened
- For `https://weibo.com/2105171747/QERW9iBjT` and `https://weibo.com/2105171747/QES0ucwwt`, the persistent Playwright profile remained logged in and could like/comment successfully.
- One run reported it could not find the comment composer, but direct Playwright inspection showed `textarea[placeholder="发布你的评论"]` existed and the page had a clickable `button:has-text("评论")`.
- Verifying via `body.innerText` after switching comment sorting to `按时间` confirmed the new comment was present in the live comment list.

## Useful technique
- If the helper script says the composer is missing, inspect `button` and `textarea` elements directly.
- The effective fallback was:
  1. load the post in the seeded persistent profile
  2. ensure the post is liked
  3. fill `textarea[placeholder="发布你的评论"]`
  4. click `button:has-text("评论")`
  5. switch to `按时间`
  6. verify the new comment in `body.innerText`
  7. capture the evidence screenshot

## Screenshot takeaway
- The user-facing default remained the contextual boxed screenshot.
- The full-page boxed screenshot showed more context, but the contextual boxed image was usually the better handoff artifact for Telegram because it stayed tighter and easier to read.
- Keep full-page boxed as a secondary artifact when the contextual crop is readable but you want extra context for debugging or manual verification.
