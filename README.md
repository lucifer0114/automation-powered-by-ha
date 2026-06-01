# weibo-comment-evidence-snapshot

Snapshot of the Weibo comment evidence workflow, now versioned through GitHub releases for traceable reliability iterations.

## Included
- Hermes skill: `skill/SKILL.md`
- Skill references: `skill/references/*.md`
- Playwright script: `script/weibo_manual_comment_flow.py`
- Regression tests: `tests/*.py`

## Purpose
- preserve a clean standalone repo for iterative hardening
- make each verified milestone easy to reference from GitHub Releases
- keep script, skill notes, and regression coverage aligned

## Current release
- Latest: [`v1.0.1`](https://github.com/lucifer0114/weibo-automation-powered-by-ha/releases/tag/v1.0.1)
- Previous baseline: [`V1.0.0`](https://github.com/lucifer0114/weibo-automation-powered-by-ha/releases/tag/V1.0.0)

## What `v1.0.1` adds
- structured single-line evidence output via `EVIDENCE=<json>`
- final run summary output via `FINAL_SUMMARY=<json>`
- stronger wait / submit verification hardening in the comment workflow
- expanded regression coverage for evidence and reliability behavior

## Notes
- This repository was exported from the local Hermes environment and then iterated independently
- Runtime-specific paths inside the skill/script are intentionally preserved as-is
