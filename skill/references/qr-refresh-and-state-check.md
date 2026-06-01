# QR refresh and state-check notes

Session takeaways:

- `browser_snapshot()` may briefly return `(empty page)` during Weibo login/post transitions. Do not assume the page is dead; re-check with `browser_console` and `browser_vision`.
- Weibo QR login cards in this environment often do **not** expose a visible refresh/reload icon next to the QR code.
- The most reliable way to regenerate a QR login state is to **re-open the login entry** or **re-navigate to the target URL** so Weibo reissues the QR/login page.
- If the page unexpectedly shows a different post than the intended URL, verify the post body with `browser_console` before liking/commenting.
- When the login page appears to have both QR and SMS panels, use `browser_vision` to confirm the actual visible state before deciding whether to scan or switch to SMS.
