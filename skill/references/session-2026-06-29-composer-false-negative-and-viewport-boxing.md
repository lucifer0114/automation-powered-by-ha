# Session note: composer false-negative + tight viewport boxing

## Why this matters
Two reusable failure modes showed up in the same Weibo evidence workflow:

1. the local helper sometimes claimed it could not find the comment composer even though the live page still had a visible `textarea[placeholder="发布你的评论"]` and a visible `button:has-text("评论")`
2. a first-pass screenshot could find the right comment text but still place the red box on the wrong visual block, or include too much unrelated comment area

## Durable lessons

### 1) Treat helper composer misses as a probe, not a verdict
If the scripted helper says it cannot find the composer:
- re-probe the live page directly in the same persistent-profile context
- check `textarea[placeholder="发布你的评论"]`, generic `textarea`, and `button:has-text("评论")`
- if those controls are visibly present with real bounding boxes, bypass the helper path and submit directly through those locators instead of retrying the same helper workflow

This was validated on:
- `https://weibo.com/2449552120/R660FiVpG` (`王玉雯Uvin`)
- `https://weibo.com/1662068793/R5SegvEqC` (`唐艺昕`)

In both cases the helper path had a false negative, while direct DOM interaction succeeded.

### 2) For disputed boxing, rebuild from viewport coordinates
If the user says the red box is wrong, do not defend the first artifact.

Recovery pattern:
1. reopen the post in a fresh persistent-context page
2. switch to `按时间` when needed and confirm the target comment again
3. scroll so the whole post card is visible in a single viewport
4. take a viewport screenshot
5. crop from viewport coordinates, not stale full-page/document coordinates
6. draw the box from the live visible comment container (`.con1` preferred, `.text` if needed)
7. visually verify before delivery

This is safer than mixing document-space coordinates from one layout phase with screenshots from another layout phase.

### 4) Header-inclusive composition is the new default
For this user's current acceptance bar, a screenshot is incomplete if it shows only the post body + comment but cuts off the publishing account/header.

Accepted composition target now is:
- publishing account header visible
- full post body visible
- interaction row visible when layout allows it
- only a small slice of the comment area
- red box on the exact target comment

A practical default crop for this style is:
- horizontal bounds: article/shell left/right ± small padding
- top: high enough to include the publishing account header, not just the正文 block
- bottom: target comment card bottom + small padding

If the first crop misses the header, treat it as incomplete and rebuild before delivery.

## Concrete pattern
When the target comment is already visible in the same viewport as the full post card:
- use the viewport screenshot as the source image
- crop to the article bounds plus just enough space to include the target comment card
- draw the red box from the visible `.con1` bounds rather than a looser parent container unless the tighter box cuts off timestamp/author context

## What not to do
- do not trust the first boxed artifact if the user says it is wrong
- do not keep a loose crop just because the comment is technically present somewhere on screen
- do not rely on the helper’s composer miss after direct probing proves the controls are visible
