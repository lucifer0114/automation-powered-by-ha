# Structured Output Contract

Use this note when the local Weibo evidence script is being consumed by another script, cron job, or agent.

## Stdout signals

### `EVIDENCE=<json>`
Emitted during the run for step-level machine-readable events.

Current event families:
- `type: "wait"`
  - includes `context` such as `initial-load`, `after-submit`, `before-locate-comment`
  - includes `result` such as `networkidle`, `selector:...`, `timeout-fallback`
- `type: "like"`
  - includes `status`, `selector`, `state`
- `type: "submission"`
  - includes `submit_selector`, `wait_result`, `login_required`, `comment_visible`

Use these for timeline/debug detail, not as the single source of final success.

### `FINAL_SUMMARY=<json>`
Emitted once at the terminal status boundary.

Treat this as the primary machine-readable verdict for the run.

Important fields:
- `status`
  - currently includes values such as:
    - `ok`
    - `login-required-initial`
    - `login-required-after-submit`
    - `submission-not-confirmed`
    - `login-required-before-capture`
    - `comment-not-found`
    - `comment-found-no-box`
- `wait.initial_load`
- `wait.after_submit`
- `wait.before_locate_comment`
- `like_status`
- `submission_confirmed`
- `comment_found`
- `login_required`
- `primary_mode`
- `final_screenshot`

## Consumption guidance

- Prefer `FINAL_SUMMARY` for pass/fail routing.
- Use `EVIDENCE` events when diagnosing why a run failed or took a fallback path.
- Do not infer final success from `RAW_SCREENSHOT=` or `BOXED_SCREENSHOT=` lines alone; read `FINAL_SUMMARY.status` and `submission_confirmed`.
- For fast automation, the minimum useful parse is:
  1. last `FINAL_SUMMARY=<json>` line
  2. if failure, the preceding `EVIDENCE=<json>` events for context
