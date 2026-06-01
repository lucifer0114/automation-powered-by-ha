# Abnormal-behavior verification flow

Observed in this session:
- A Weibo post page can load normally with valid cookies, yet the page still blocks interaction with the message: `你的账号异常行为频率较高，暂无法进行发博、发评、关注、点赞等操作，可在验证身份后恢复。`
- In this state, the visible `评论` button may be disabled even though the post body and comments are rendered.
- This is an action restriction, not necessarily an expired-login problem.

How the page routes the user:
- Clicking `登录/注册` on the post page opens the combined verification/login panel.
- The panel can show:
  - `扫描二维码登录`
  - `验证码登录`
  - `账号登录`
  - `+86`
  - `手机号`
  - `验证码`
  - `获取验证码`
  - `登录/注册`
- The QR/login panel may appear even when `browser_snapshot()` is empty; use `browser_vision()` or `browser_console` text probes to confirm the live UI.

Practical recovery rule:
- Treat a valid cookie state + disabled interaction buttons + abnormal-frequency message as a *risk-lock* flow.
- After verification, always re-open the target post and re-check whether `评论`/`点赞` are actually enabled.
- Do not assume that returning to the post page means the risk lock is gone.

Useful console probe:
```js
[...document.querySelectorAll('button,a,div,span')]
  .map(el => (el.innerText || '').trim())
  .filter(Boolean)
  .filter(t => t.includes('异常') || t.includes('验证') || t.includes('获取验证码') || t.includes('登录/注册'))
```
