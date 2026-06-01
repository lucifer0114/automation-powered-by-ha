# Static review — reliability risks in `weibo_manual_comment_flow.py` (2026-06-02)

Condensed findings from a static review of the local Weibo evidence script.

## Highest-priority fixes

1. **Do not treat "found the same comment text somewhere on the page" as proof that the current submit succeeded.**
   - Same text may already exist from an older comment, another user's comment, or the still-filled composer.
   - Prefer: record pre-submit state, then verify a *new* comment item appears under the current account after submit, ideally in `按时间` order with a fresh timestamp / newest position.

2. **Do not use the same broad `评论` click helper for both opening the comment UI and submitting the comment.**
   - Weibo pages often contain multiple `评论` affordances.
   - Keep separate helpers for:
     - opening / expanding the comment area
     - submitting the filled composer near the target input box

3. **Constrain comment matching to the comment list / comment card region.**
   - Avoid whole-page `.first` matches over `div/span/p:has-text(...)`.
   - Exclude composer / editable regions and prefer matching inside a verified comment item container that also contains author / timestamp / interaction controls.

4. **Verify login / page state explicitly before like / comment / capture.**
   - Persistent profile reuse is helpful but not sufficient.
   - Detect visitor/login pages, QR / SMS auth surfaces, abnormal-frequency verification panels, and stale landing pages before acting.

## Secondary fixes worth doing

- Verify `按时间` switch actually took effect instead of treating a click attempt as success.
- Scope like-button detection to the confirmed main post container, not the first generic article/card.
- Confirm the filled text is in the intended composer before trying to submit.
- Guard `highlight_box` / crop-box generation with null and geometry validation; fall back to `text_box` when the expanded card box cannot be derived.
- Treat `networkidle` only as a weak signal on Weibo; rely more on concrete DOM state (main post visible, comment area expanded, composer editable, newest comment item present).
- If red-box coordinates are computed before a full-page screenshot, re-check layout stability because lazy rendering / reflow can shift the target.

## Why this matters

This workflow produces user-facing proof screenshots. In this class of task, a false-positive success or a boxed screenshot around the wrong node is worse than a hard failure, because it creates misleading evidence.
