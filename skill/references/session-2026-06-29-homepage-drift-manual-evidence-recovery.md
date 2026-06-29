## What happened

- On post `https://weibo.com/2606218210/QEsqWrUA6`, the main helper script successfully liked the post but then reported it could not find the comment composer.
- A direct Playwright probe against the same persistent profile showed the page body was still the correct post page, `textarea[placeholder="发布你的评论"]` existed, and a forced click on `button:has-text("评论")` submitted the comment successfully.
- The submitted test comment was `支持一下，顺手留个小脚印🌿06290853`, and a follow-up DOM/body-text check after switching to `按时间` confirmed the fresh comment item with timestamp `26-6-29 08:53 来自山西`.
- The script's later `--capture-only` pass drifted into a bad visual state and produced a raw screenshot of the 微博首页/home feed instead of a valid post-evidence image, even though the persistent-profile probe still showed the real post page and the fresh comment in the DOM.

## Durable lesson

- Treat a homepage/feed raw screenshot after `--capture-only` as a page-state drift, not as proof the comment is missing.
- When this happens, reopen the post in a fresh persistent-context page, switch to `按时间`, and verify the fresh comment again via `body.innerText` / structured comment-card probe before doing evidence recovery.
- If the verified post page and comment are present, save a fresh full-page screenshot from that verified page and manually crop / red-box from the known post card + comment-card coordinates rather than trusting the stale helper output.
- For this failure shape, the reliable source of truth was the direct Playwright probe (`locator('textarea[placeholder="发布你的评论"]')`, `button:has-text("评论")`, `body.innerText`), not the helper's capture-only screenshot.

## Recovery recipe

1. Reopen the target URL in the persistent Weibo profile.
2. Confirm the post body text still matches the requested post.
3. If needed, click `按时间` so the fresh comment is at the top.
4. Confirm the fresh comment by exact text plus fresh timestamp/account context in the live body text.
5. Save a new full-page screenshot from this verified page.
6. Build the user-facing artifact by cropping the post card + interaction row + top of the comment list, then draw the red box around the verified comment item.

## Why this matters

The failure was not "comment missing"; it was "helper capture path drifted to the wrong visual page." The skill should fail closed on stale helper screenshots and prefer a verified reprobe + manual boxing path over falsely telling the user the capture failed.