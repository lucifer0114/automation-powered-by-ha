# Session Pitfalls

## User-specific delivery defaults
- The user wants every Weibo comment response to include a screenshot.
- The user prefers the boxed/contextual proof image, not raw or full-page screenshots.
- The user wants posts liked before the proof screenshot is taken.

## What tripped this session
- A few attempts returned a login wall instead of the post page; in that state, commenting and screenshot capture cannot proceed.
- One auto-submit run stalled because the script could not find the comment input in the current browser state and fell back to an interactive prompt, which is unusable in headless/non-interactive execution.

## Practical handling
- Prefer the contextual boxed artifact as the user-facing deliverable.
- If the page falls back to login/visitor flow, stop and ask for a fresh logged-in browser state rather than pretending the comment was posted.
- If submission is needed and the comment box is not found automatically, retry in a visible browser session or confirm the page is fully loaded before attempting to submit again.
