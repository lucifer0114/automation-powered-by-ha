# Session note: login-state check + comment recovery

## What happened
- `browser_navigate()` to a Weibo post can land on `Sina Visitor System` even when the persistent Playwright profile still works.
- A separate Playwright persistent context using `/home/aimashi/.playwright-weibo-profile` successfully opened the post body page and showed no QR / abnormal / visitor banner.
- For the post `https://weibo.com/2606218210/QEsqWrUA6`, re-posting the comment worked through the terminal-based Playwright flow, and the resulting screenshot was acceptable after a tighter crop.

## Useful recovery pattern
1. If a navigation helper returns a visitor page, verify login state with a fresh persistent-context page before assuming the session is broken.
2. Prefer `body.innerText()` after switching to `按时间` to confirm the fresh comment exists.
3. If exact text locators fail, scroll and re-check the full body text; the comment can be present even when the locator count is 0 until the right viewport state is reached.
4. Use a tighter contextual crop centered on the comment item rather than a loose full-page capture.

## Evidence crop note
- A text-only red box around the comment text can be enough when the body + comment list are visible and the comment is unambiguous.
- If the user requests stricter proof, expand the box to include avatar, nickname, and timestamp for the full comment unit.
