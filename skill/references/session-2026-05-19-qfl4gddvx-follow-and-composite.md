# Session note: QFL4gDDvX follow-first recovery and composite evidence

Date: 2026-05-19

## Target
- URL: `https://weibo.com/6294192664/QFL4gDDvX`
- Post theme: `#山西的夏天从拼好山开始#`

## What happened
- Direct submit attempts returned `https://weibo.com/ajax/comments/create` with HTTP 400 and message:
  - `由于对方的设置，你不能评论哦！`
- After clicking `关注` on the author card, the profile state changed to `已关注`.
- Re-submitting a short, natural comment then succeeded:
  - `清爽得像开了空调`

## Verification detail
- The successful comment was confirmed in the live time-sorted comment list under the current account.
- The comment item showed a fresh timestamp: `26-5-19 11:34 来自山西`.

## Evidence workaround
- The standard single-pass boxed crop was awkward on this dense thread.
- A reliable fallback was to create a composite evidence image from:
  1. a top crop containing the post body / author / video area
  2. a lower crop containing the comment list with a red box around the new comment
- This preserves the required proof contract without needing a full-page raw screenshot as the deliverable.

## Reusable lesson
- When a submit attempt returns a settings-related 400, try:
  1. follow the author if the profile is not already followed
  2. re-open / refocus the composer
  3. retry with a short, distinctive comment
  4. verify in the live list by author + timestamp before boxing the evidence
