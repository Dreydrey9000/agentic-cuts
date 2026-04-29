---
name: avatar-dub-render
description: Stage 6 (final) of avatar-dub. Final encode + delivery promise gate + post-render audit. Always pauses for human approval.
---

# avatar-dub / render

**Input:** `dubbed_clip` from lip-sync.
**Output:** `final_dubbed_clip` (publish-ready MP4) + `render_report`.
**Approval:** REQUIRED. Drey signs off before any publish action.

## What you do

1. Run the pre-compose `validate_plan(promise, plan)` gate. Hard-fail any duration / aspect / motion mismatch.
2. Encode with the target media profile via FFmpeg. Default `tiktok` (1080x1920, 30fps, libx264, +faststart, yuv420p).
3. Audio normalization to target LUFS (default -16 for short-form social). Match the SOURCE clip's LUFS if it was higher quality.
4. Post-render audit: ffprobe + 10-frame sample + audio level analysis.
5. Save `render_report.json` with: encode duration, file size, LUFS, drift report from lip-sync stage, decision log of every selector choice.
6. Pause for human approval with the report inline.

## Review focus

- ffprobe matches target profile.
- Audio LUFS within ±1 dB of target.
- File size sane (2MB-60MB for 30-90 sec).
- Drift report attached and within budget.

## What you do NOT do

- No re-render of the lip-sync stage — re-run upstream if drift is bad.
- No auto-publish — Drey signs off, then downloads + posts via his scheduler.
- No watermark unless the brand kit's `logo` says so.
