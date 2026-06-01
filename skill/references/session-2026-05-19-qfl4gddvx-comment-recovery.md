# Session note: QFL4gDDvX comment recovery

Date: 2026-05-19

## Situation
- Target post: `https://weibo.com/6294192664/QFL4gDDvX`
- Post theme: Hi山西, `#山西的夏天从拼好山开始#`
- Like action succeeded.
- Comment submission / recovery was unstable.

## Observed behavior
- `comments/create` returned `400` in at least one attempt.
- The page body contained many existing comments with near-duplicate phrasing about 山西的夏天 / 山风 / 治愈感.
- The exact candidate comment text did not reliably appear as a fresh, uniquely attributable item in the comment list.
- A later body scan showed phrases like `太治愈了`, suggesting one of the shorter variants may have landed even though the original wording did not stabilize.

## Reusable recovery pattern
1. Keep the like-first workflow.
2. If the comment list is dense with similar praise, prefer a shorter and more distinctive comment.
3. After submit, switch to `按时间` and verify the new item by author + timestamp, not by matching a sentence that may already appear elsewhere.
4. If the exact text cannot be isolated, use `body.innerText` plus a fresh scroll to inspect the live list before retrying.
5. If `comments/create` returns `400`, try a shorter rewrite before repeating the same comment.

## Good candidate style for this post family
- Short, natural, and specific.
- Avoid common phrases already saturated in the thread such as `山西的夏天太治愈了` or `一山一风景` unless the goal is only rough sentiment matching.
- Prefer distinctive snippets like:
  - `山风真舒服`
  - `这夏天也太舒服了`
  - `看着就很清爽`

## Note
- Do not treat a later appearance of a common phrase elsewhere in the page body as proof of a new submission.
- The reliable success condition is a fresh comment item in the live list under the current account after time-sorting.
