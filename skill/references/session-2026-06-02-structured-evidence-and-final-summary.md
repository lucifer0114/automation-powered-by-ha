# Structured evidence + final summary logging

This session hardened the local Weibo evidence script's stdout contract for downstream automation.

## What was added
- Structured single-line event logs:
  - `EVIDENCE=<json>`
- Final roll-up line at the end of each terminal path:
  - `FINAL_SUMMARY=<json>`

## Event payloads now covered
- `type=wait`
  - emits page-readiness results such as `networkidle`, `selector:...`, or `timeout-fallback`
  - useful contexts include `initial-load`, `after-submit`, and `before-locate-comment`
- `type=like`
  - records like status, selector used, and observed button state
- `type=submission`
  - records submit selector, post-submit wait result, whether login/risk-control was detected, and whether the comment was confirmed visible

## Final summary intent
Use `FINAL_SUMMARY` as the first machine-read target when parsing a run. It should summarize:
- terminal status (`ok`, `comment-not-found`, `submission-not-confirmed`, `login-required-*`, etc.)
- all major wait outcomes
- final like status
- whether submission was confirmed
- whether the comment was found for capture
- whether login/risk-control blocked completion
- primary artifact mode
- final screenshot path

## Implementation guidance
- Emit the final summary on both success and guarded early-exit paths.
- On failure paths that save a raw screenshot for diagnosis, set `final_screenshot` to that artifact.
- Keep the payload single-line JSON so shell pipelines and follow-up agents can parse it reliably.
- Preserve the existing human-readable prints; the structured lines are an additional contract, not a replacement.

## Why this matters
This avoids log-scraping fragile natural language when a later agent or script needs to answer:
- Did submit verification pass?
- Which readiness path actually succeeded?
- Did the flow end in login/risk-control?
- What screenshot should be returned or inspected next?
