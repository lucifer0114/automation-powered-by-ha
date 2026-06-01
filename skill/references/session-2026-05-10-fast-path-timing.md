# Session note: fast-path timing and evidence quality

## What changed
We tested a faster capture path for Weibo evidence on `https://weibo.com/7850154169/QEpZx01rs`.

## Observed timing
- Page load wait: about 3.5s
- Submit/post wait: about 2.5s to 5.5s depending on whether the comment was being posted or only captured
- End-to-end successful fast-path example: about 9.95s total

## Important finding
The faster path was only reliable when the comment existed as an exact DOM text hit. If the exact text was missing, broad crops and guessed boxes produced weaker evidence.

## Practical rule
- Prefer a short initial wait
- Sort comments by `按时间`
- Require an exact comment-text anchor before cropping
- If exact text is not found, stop and re-check the live page rather than emitting a loose box

## Example successful evidence comment
- `山西真是越看越有味道。`

## Outcome
The faster path improved turnaround and still produced an acceptable boxed contextual screenshot when the exact comment was present.