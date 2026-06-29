# Duplicate-comment fast-path regression (2026-06-02)

## What changed
A third-layer speed optimization reduced evidence capture time by:
- shortening waits
- preferring direct composer access
- deferring `按时间` until needed
- taking the contextual screenshot directly from the computed crop box instead of always saving a full-page image and then recropping

A real run brought `capture-only` latency down from roughly 9s to about 7s.

## Regression discovered
On posts where the same comment text appears more than once in the thread, the faster evidence path can regress in correctness:
- box the wrong duplicate comment lower in the thread
- crop out the post body
- degrade into an oversized or weakly anchored box

## Durable lesson
Speed wins are not enough for this workflow. The boxed contextual screenshot is only acceptable if visual verification still confirms all three:
1. post body visible
2. comment area visible
3. red box tightly anchored to the topmost target comment, not a duplicate or oversized region

## Preferred fix direction
When duplicate comments are possible, move from text-hit-first matching to comment-card-first matching:
1. enumerate the smallest stable comment-card/container nodes available on the page
2. score cards by current-account author, fresh timestamp/day marker, and topmost position after `按时间` when needed
3. draw the evidence box from the winning comment card's own bounds, not from a broad ancestor expansion
4. only keep direct contextual clip as the final fast path after the image passes the three-part visual check above

## Operational rule
If a new performance optimization makes evidence faster but introduces duplicate-comment ambiguity, do not declare the optimization complete. Keep the older slower-but-correct branch, or add a fallback branch, until the boxed contextual screenshot is again unambiguous.