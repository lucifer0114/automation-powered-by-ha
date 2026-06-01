# Raw-to-contextual recovery when `BOXED_SCREENSHOT=NOT_FOUND`

Session pattern:
1. A `--capture-only` run may save only `RAW_SCREENSHOT=..._raw.png` and report `BOXED_SCREENSHOT=NOT_FOUND` even though the comment exists.
2. Re-running the same URL/comment with `--submit --like --headless` often succeeds on the second pass and emits `CONTEXT_BOXED_SCREENSHOT=..._context_boxed.png`.
3. If the script still fails to match the comment text, use the raw screenshot for visual diagnosis:
   - split the long page into vertical bands
   - build a contact sheet
   - use vision to narrow the likely comment region before retrying
4. Do not trust a stale `browser_snapshot()` alone after a background run; re-open the URL or use the script output plus a fresh page check to confirm the live state.

Practical takeaway:
- Treat `BOXED_SCREENSHOT=NOT_FOUND` as a recoverable evidence problem, not proof that the comment was not posted.
- Prefer a second `--submit` pass before manual reconstruction.