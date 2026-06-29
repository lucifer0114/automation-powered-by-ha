# Session note: fast-path waits and deferred sort

## Why this matters
The local Weibo evidence script had accumulated several fixed waits and a conservative sequence that made successful runs slower than necessary:
- opening the page always tried a long `networkidle` wait first
- submit flows often clicked `评论` before even checking whether the textarea was already present
- after submit, the flow waited again before proving success
- capture-only verification switched to `按时间` too early instead of trying the current view first

The user explicitly approved a faster default path so long as reliability-preserving fallback remained in place.

## Durable pattern
Use a **fast path first, fallback second** policy:

1. Page open:
   - try a short `networkidle`
   - if it stalls, confirm readiness through concrete selectors such as post article / composer / comment button
2. Submit path:
   - try the composer directly via `textarea[placeholder="发布你的评论"]`
   - only click the visible `评论` control if the textarea is absent or hidden
3. Submit click:
   - after filling, use a short settle period and then verify via live comment presence
   - do not burn a long unconditional `networkidle` after clicking submit
4. Capture/verification:
   - first search for the fresh comment in the current view
   - only if that misses, switch to `按时间` and retry
5. Runtime trimming:
   - shorten fixed sleeps around like/panel-open/submit
   - keep reliability by coupling shorter waits with explicit fallback checks, not by deleting verification altogether

## Concrete timing reductions used in this session
These exact numbers are implementation detail, but the class-level lesson is to trim fixed sleeps before changing verification logic:
- like settle: about `1500ms -> 700ms`
- panel-open settle: about `1500ms -> 500ms`
- post-submit settle: replaced a heavier wait with a short `~1200ms` settle plus verification
- initial page readiness: replaced a long-only wait with `wait_for_page_ready()` that falls back from `networkidle` to concrete readiness checks

## Verification result from this session
A no-side-effect validation run (`capture-only`) still found the target comment and produced evidence successfully, with elapsed time around **8 seconds**.

## What to reuse next time
When a Weibo automation path is "working but too slow," optimize in this order:
1. remove or shorten unconditional sleeps
2. check direct composer availability before clicking expand controls
3. defer expensive/sorting recovery steps until the first direct lookup fails
4. keep a verification gate so speedups do not reintroduce false success
