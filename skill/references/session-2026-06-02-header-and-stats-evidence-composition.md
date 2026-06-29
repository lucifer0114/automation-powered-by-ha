# Session note — header-and-stats evidence composition

## Why this exists
A duplicate-comment capture flow produced a screenshot that still contained the boxed target comment, but the crop stopped too low/high and omitted two provenance cues the user cared about:
- the posting account header (`黄河新闻网` in this case)
- the interaction-count row (`转发 / 评论 / 点赞`, e.g. `45 / 3042 / 4481`)

The user explicitly asked to match an earlier stronger composition by including both of those layers while keeping the comment thread and red-boxed target comment visible.

## Durable lesson
For Weibo proof screenshots, "正文 + 红框评论" is sometimes necessary but not sufficient. When the goal is a stronger, screenshot-faithful proof artifact, include four layers in one contextual crop:
1. account header / publisher name
2. post body
3. interaction-count row
4. relevant comment area with the boxed target comment

## Implementation guidance
- Do not anchor the crop from the comment box alone.
- Do not anchor the crop from the正文 bounding box alone if that would trim off the account header or the interaction row.
- Score the crop against the whole post-card composition: header at top,正文 in the middle, stats row below正文, comment region below that.
- If a fixed footer / floating site control overlaps the stats row, hide it or adjust the crop so the counts remain readable in the final image.
- If a faster direct-context clip path regresses on any of these layers, fall back to the slower verified composition rather than shipping a partial proof image.

## Verification checklist
Before delivery, visually confirm all of the following are simultaneously visible:
- publisher/account name readable
- at least one line of the post body readable
- `转发 / 评论 / 点赞` row readable, including the numbers when present
- comment thread visible
- red box tightly wraps the intended target comment

## Good failure language
If the crop is faster but loses the header or stats row, report it as a correctness/composition regression rather than claiming completion.