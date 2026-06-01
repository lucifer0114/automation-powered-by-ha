# Login wall recovery notes

Session pattern observed:
- After navigating to a Weibo post, the page can briefly resolve to `Sina Visitor System` and then later render the content page.
- `browser_snapshot()` may return `(empty page)` even when the page is still recoverable; use `browser_vision()` to confirm whether the QR login card or SMS login form is visually present.
- If the user says the QR code is invalid or unavailable, open the login panel and switch to `验证码登录`.
- In some sessions, the login panel exposes both QR login and SMS login side-by-side; the SMS form contains `手机号`, `验证码`, and `获取验证码`.
- If named refs go stale after a page transition, use `browser_console` text queries or a fresh `browser_snapshot()` instead of reusing old refs.

Useful console probe for the SMS login form:
```js
[...document.querySelectorAll('button,a,div,span')]
  .map(el => el.innerText?.trim())
  .filter(Boolean)
  .filter(t => t.includes('验证码') || t.includes('获取'))
```

When the SMS form is visible:
- fill the phone field first
- click `获取验证码`
- wait for the user to provide the code before attempting final login
