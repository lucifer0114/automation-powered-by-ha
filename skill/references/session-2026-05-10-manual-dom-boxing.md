# Session note: manual DOM boxing for Weibo evidence

Date: 2026-05-10

## What happened
- On `https://weibo.com/2606218210/QEsqWrUA6`, the comment was successfully posted, but the helper script's `--capture-only` mode could not reliably locate the comment text for automatic boxing.
- The page body still contained the comment, so the failure was not a posting failure; it was a locator / evidence-matching failure.

## Recovery pattern
1. Use Playwright `body.inner_text()` or a DOM scan over `document.querySelectorAll('*')` to confirm the comment is actually present.
2. Find the smallest visible element whose text includes the target comment.
3. Record the element's bounding box from `getBoundingClientRect()`.
4. Take a full-page raw screenshot.
5. Crop a contextual region around the anchor so the screenshot still shows the post body, the comment composer, and the relevant slice of the comment list.
6. Draw the red box around the anchor-relative comment node.

## Pitfalls
- A raw full-page screenshot can contain the comment but still not be usable as evidence if the crop is too tight or omits the post body.
- Vision may say the comment is present even when the crop is not ideal; always prefer DOM coordinates when available.
- A comment string appearing in the page body is not proof of a good evidence crop by itself; the final image still needs the post + partial thread + red box.

## Useful details from this session
- The target comment that was ultimately used for evidence was: `把孩子们的荣誉戴在身上，这一幕真暖。`
- The anchor was recovered from the DOM as a `SPAN` with a bounding box near `x≈437.4, y≈811.9, w≈235.8, h≈15` in the full-page screenshot.
- The resulting contextual crop that worked best was `/home/aimashi/outputs/weibo-comment-shots/qesq_newcomment_context_boxed_v3.png`.
