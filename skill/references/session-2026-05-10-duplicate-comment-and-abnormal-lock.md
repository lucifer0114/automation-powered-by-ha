# Session note: duplicate comment ambiguity and abnormal-lock verification

## What happened
- On post `https://weibo.com/2105171747/QEgiN7S9T`, the candidate comment text `薪火相传，强军梦想在少年心中生根发芽。` already existed elsewhere on the page as an older comment / page text, so the same sentence could not be used as proof of a newly posted comment.
- Another attempted comment (`从讲台到军校，这种接力特别燃。`) did not show up in the comment list after submit attempts.
- The page intermittently showed:
  - `你的账号异常行为频率较高，暂无法进行发博、发评、关注、点赞等操作，可在验证身份后恢复。`

## Operational lessons
- Do not accept a comment as successfully posted just because its text appears somewhere in the page body.
- For evidence, require the new comment to be visible in the comment list under the current account, ideally after switching to `按时间` if available.
- If the same text already exists in old comments or page content, use a more unique comment or disambiguate with author + timestamp, not body text alone.
- If the abnormal-frequency banner is still present after a submit attempt, treat the session as action-restricted and stop retrying the same submit path repeatedly; move to verification / re-auth handling instead.
- A successful proof screenshot should show the post body plus the new comment item; avoid screenshots that only capture the post body or pre-existing comments.
