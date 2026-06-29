# Changelog

All notable changes to this repository are documented in this file.

## [Unreleased / v1.0.4]

### Changed
- hardened the submit path against composer false negatives by adding a direct DOM composer probe/recovery branch when standard locators miss a live textarea
- widened the default contextual crop upward so the publishing account/header is included together with the post body, interaction row, and boxed target comment
- kept the faster v1.0.4 wait strategy while folding in the real smoke-run lesson from the `黄河新闻网` post recovery

### Added
- regression coverage for the direct DOM composer fallback when visible composer controls are missed by the helper path
- regression coverage for the header-inclusive crop-box computation used by the contextual screenshot path

## [v1.0.3] - 2026-06-29

### Changed
- synced the repository to the current live `weibo_manual_comment_flow.py` workflow used in production runs
- updated the regression tests to match the current script surface so the checked-in suite verifies the maintained workflow instead of an older API
- refreshed the README so the release line, tighter screenshot standard, and speed-priority constraints are documented from the repo root

### Added
- the latest skill reference notes covering direct-textarea fallback, deferred time-sort waits, duplicate-comment handling, viewport-based red-box recovery, homepage-drift recovery, and the newer tight-crop/speed guidance
- a `v1.0.3` source snapshot of the current stable Weibo evidence baseline for GitHub release archival

## [v1.0.2] - 2026-06-02

### Changed
- updated the README to reflect the current release line and version progression
- aligned repository-facing wording to a cleaner, lower-exposure presentation while keeping the release trail intact

### Added
- `docs/plans/2026-06-02-v1.0.2-development-checklist.md` as a dedicated checklist for the next hardening cycle
- a clearer planning summary for the next milestone: shared finalization, machine-readable artifact output, stronger submission verification, and cleaner downstream artifact metadata

## [v1.0.1] - 2026-06-02

### Added
- structured single-line evidence output via `EVIDENCE=<json>`
- final run summary output via `FINAL_SUMMARY=<json>`
- expanded regression coverage for evidence and reliability behavior

### Changed
- stronger wait and submission-verification hardening in the automation flow
- better overall workflow stability through more explicit readiness and verification handling

## [V1.0.0] - 2026-06-02

### Added
- initial standalone source snapshot of the automation bundle
- bundled skill assets under `skill/`
- primary Playwright automation script under `script/`
- baseline regression tests under `tests/`

[v1.0.3]: https://github.com/lucifer0114/automation-powered-by-ha/releases/tag/v1.0.3
[v1.0.2]: https://github.com/lucifer0114/automation-powered-by-ha/releases/tag/v1.0.2
[v1.0.1]: https://github.com/lucifer0114/automation-powered-by-ha/releases/tag/v1.0.1
[V1.0.0]: https://github.com/lucifer0114/automation-powered-by-ha/releases/tag/V1.0.0
