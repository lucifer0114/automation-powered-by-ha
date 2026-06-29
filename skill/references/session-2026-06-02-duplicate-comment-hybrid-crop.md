# Duplicate-comment evidence capture: structured match + same-column post crop

Use this pattern when a Weibo thread contains the same comment text more than once and evidence screenshots must still show the correct topmost target comment plus the original post body.

## Problem pattern

A naive fast path can regress in two different ways:

1. **Wrong comment box**
   - exact text search finds a later duplicate comment instead of the newest/topmost one
   - matching `.text` / `span` nodes can box only the sentence, not the full comment card

2. **Wrong post-body crop**
   - a broad post selector such as `.woo-panel-main` can resolve to the right sidebar / hot-search panel instead of the main post column
   - the final crop then contains comments but little or no real post body

## Durable fix

### 1) Match the comment by card structure first
Prefer full comment-card selectors before generic text hits:
- `.item1`
- `.wbpro-scroller-item`
- `.vue-recycle-scroller__item-view`
- `.item1in`
- `.con1`

Ranking heuristics that worked well:
- prefer cards containing today's timestamp/date token
- prefer cards in the topmost position after switching to `按时间`
- prefer cards where the exact comment text appears once
- only fall back to generic `text=` / `div:has-text(...)` matching after structured card matching fails

### 2) Constrain post-body selection to the same column as the matched comment
When choosing the post-body region, do **not** just take the first visible `.woo-panel-main`.

Instead:
- prefer `.wbpro-feed-content`, then `article`, then `.woo-panel-main`
- require substantial horizontal overlap with the matched comment card, or near-identical left edge
- penalize narrow panels and non-main-column candidates
- choose the candidate above the matched comment in the same content column

This avoids accidentally cropping the right sidebar or hot-search module.

### 3) Hybrid screenshot strategy for quality
For duplicate-comment pages, the best trade-off was:
- keep **fourth-layer correctness** for comment matching (structured card target)
- keep **third-layer composition goals** for the screenshot (tight contextual crop)
- crop from a stable full-page base when needed, but keep margins tight enough that the result still feels like a contextual evidence image rather than a loose diagnostic crop

Recommended crop behavior:
- include the post body text area
- include only the relevant upper part of the comments section
- keep the topmost matched comment fully visible
- keep horizontal and vertical margins deliberately tight; do not over-pad just because the full-page base is available

## Verification checklist

A candidate image is acceptable only if all are true:
- visible post body text from the target Weibo
- visible comment area
- red box surrounds the **topmost intended comment card**, not just an inner text span
- crop does not drift to sidebars / hot-search panels
- composition is reasonably tight and readable, not an obviously loose safety crop
