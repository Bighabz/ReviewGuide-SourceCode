---
phase: 18
slug: ai-image-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (via next.js) |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- --reporter=verbose imageAssets` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Verify file exists and is under 200KB via bash `ls -la`
- **After every plan wave:** Run `cd frontend && npm run test:run -- imageAssets`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | IMG-01 | filesystem | `ls -la public/images/categories/*.webp \| wc -l` | N/A | ⬜ pending |
| 18-01-02 | 01 | 1 | IMG-02 | filesystem | `ls -la public/images/mosaic/*.webp \| wc -l` | N/A | ⬜ pending |
| 18-01-03 | 01 | 1 | IMG-03 | filesystem | `find public/images/categories public/images/mosaic -name "*.webp" -size +200k` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*No Wave 0 test infrastructure needed. Verification is filesystem-based (file existence, file size). Optionally: `frontend/tests/imageAssets.test.ts` for CI.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual consistency across all images | IMG-01, IMG-02 | AI image quality is subjective | Open all generated images side-by-side in browser, check consistent lighting/color/style |
| Bold & colorful aesthetic matches vision | IMG-01, IMG-02 | Design judgment | Compare against Shopify free-trial page energy level |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
