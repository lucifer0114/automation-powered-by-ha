# Session note: `去验证` opens a separate drag-captcha tab

## What happened
- On a Weibo risk-locked post page, clicking `去验证` did **not** replace the current page in place.
- Instead, a new tab opened at a `security.weibo.com/captcha/geetest?...` URL while the original post tab remained intact.
- The new tab title was `请先验证身份`.
- The verification UI was a drag-style / avoid-obstacle captcha, not a QR login panel.

## Practical implications
- Do not assume the original post tab has changed state just because `去验证` was clicked.
- After clicking `去验证`, enumerate open pages/tabs and inspect their URLs/titles.
- The old post tab can still show the original comment list and abnormal banner while the real verification lives in the new captcha tab.
- Use visual inspection for the captcha tab; the page may expose a canvas-based widget (`yidun_avoid-canvas`) and an obstacle image (`yidun_avoid-front`).

## Useful selectors / probes
- Page title: `请先验证身份`
- URL pattern: `security.weibo.com/captcha/geetest`
- DOM hints:
  - `canvas.yidun_avoid-canvas`
  - `img.yidun_avoid-front`
  - text: `拖动左下白色排球，躲避障碍击中`

## Recovery sequence
1. Open the risk-locked post page.
2. Click `去验证` once.
3. Check `ctx.pages` / open tabs.
4. Switch to the new captcha tab.
5. Let the user complete the verification.
6. Re-open the original post tab and re-check whether `评论` / `点赞` are enabled.

## Why this matters
Earlier attempts that only re-read the original page looked like the verification had failed, when in fact the real captcha had opened in a separate tab.
