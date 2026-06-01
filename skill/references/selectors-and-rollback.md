# Weibo selectors and rollback notes

Session-derived helpers for the standardized Weibo evidence workflow.

## Reliable selectors observed

- Like button on post page:
  - `article button[title="赞"]`
  - fallback: `article .woo-like-main`
- Comment sorting toggle:
  - `text=按时间`
- Target comment area when locating a freshly posted self-comment:
  - search the page after switching to `按时间`
  - prefer the comment item container, not just the text span

## Safe like rule

- Check whether the like state is already active before clicking.
- If already liked, do not click again; avoid toggling the like off.
- Record `LIKE_STATUS=already-liked` when detected.

## Comment rollback rule

If a wrong/off-topic comment was published:
1. Switch comments to `按时间`.
2. Find the newest matching self-comment.
3. Open the comment actions menu.
4. Click delete.
5. Confirm the deletion dialog.
6. Verify the comment text count dropped to zero before reposting.

## Evidence capture rule

- Primary image should be a contextual crop containing:
  - the post body
  - a partial comment area
  - the red box around the user's own comment item
- Do not use a full-page screenshot as the main deliverable unless explicitly requested for debugging.

## Finish rule

- After posting / liking / capturing, close the page or browser context.
- Keep the persistent profile intact so login state remains available without re-authentication.
