# QR Login Capture Checklist

Use this when Weibo blocks the post behind a login wall and the user expects a QR-code screenshot to scan.

## Goal
Return a screenshot that *actually contains the QR code*, not a visitor-system blank page or a normal content page mislabeled as login evidence.

## Preferred checks
1. Open the live page with the existing browser session.
2. If `browser_snapshot()` is empty or ambiguous, do not assume the page is useless.
3. Use `browser_vision` to confirm whether the QR is visually present.
4. If the QR is visible, capture and send that screenshot immediately.
5. If the page is on `Sina Visitor System` or another redirect, retry the target post URL after a short wait.
6. After scanning, re-check the page state before continuing with like/comment/capture.

## Pitfalls from this session
- A screenshot can be visually non-blank but still be the wrong page.
- A login-wall redirect may not preserve the post page immediately after scan.
- Do not tell the user they can scan a screenshot unless the QR is clearly visible in it.

## Handoff rule
If the user says the screenshot has no QR, recapture from the actual QR login page before proceeding.