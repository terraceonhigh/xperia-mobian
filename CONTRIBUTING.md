# Contributing & Documentation Standards

This is a hardware porting project. Mistakes are expensive — a bad flash can require physical button combos to recover, and some operations (partition writes, bootloader changes) can brick the device. Documentation exists to prevent repeating failures and to let anyone pick up where the last session left off.

## Documentation Principles

1. **Record what failed, not just what worked.** A failed approach with a root cause is more valuable than a working approach without context — it prevents the next person from trying the same thing.

2. **Include the raw evidence.** Paste dmesg lines, error codes, register values. Don't paraphrase hardware output — the exact bytes matter.

3. **Separate facts from theories.** Use "confirmed" vs "likely" vs "untested." If you didn't verify it on the actual hardware, say so.

4. **Date everything.** Hardware state changes between sessions. A finding from Tuesday may not apply on Wednesday if someone flashed a different image.

5. **Name the artifacts.** Every boot image, rootfs dump, firmware file, and DTS variant should be identified by exact filename, path, timestamp, and what it contains. Ambiguous names cause the wrong image to be flashed (see: boot-mobian-touch.img disaster of 2026-03-16).

6. **Document the full reproduction path.** From source files → build commands → output artifact → flash command → verification. Someone should be able to rebuild any artifact from the repo without tribal knowledge.

7. **Record rollback procedures.** Before attempting any change, document how to undo it. For boot images, this means noting which image is currently on boot_a so it can be restored.

## File Organization

```
research/              — Investigation notes, one file per topic
  bluetooth.md         — BT bring-up findings, attempts, current status
  battery-charging.md  — Charger PMIC research
  usb-ecm.md          — USB networking research
DEVICE_STATUS.md       — Current working state + recovery procedure (the "start here" doc)
CLAUDE_STARTUP.md      — How to set up Claude Code for autonomous work
CONTRIBUTING.md        — This file
CLAUDE.md              — Build system reference and guardrails
build.sh               — Reproducible boot image build
patch-*.py             — DTS patch scripts (each one documented with what it changes and why)
build/                 — Build artifacts (gitignored, but referenced by name in docs)
images/                — Archived images (gitignored, referenced in recovery docs)
```

## Research Document Template

Each file in `research/` should follow this structure:

```markdown
# Feature — Device

**Date**: YYYY-MM-DD
**Status**: [Research | Patch ready | Tested working | Tested failed | Blocked]

## Summary
One paragraph: what we're trying to achieve, current state, key blocker.

## What We Tried
Chronological list of attempts with:
- What was changed (exact DTS node, config option, file)
- What we expected
- What actually happened (paste dmesg, error codes)
- Why it failed (root cause if known, theory if not)

## Current Understanding
What we know to be true (confirmed on hardware) vs what we believe (theory).

## Artifacts
Boot images, patch files, config diffs — with exact filenames and paths.

## Next Steps
What to try next, in priority order. Include prerequisites (kernel rebuild, firmware, etc.)

## Rollback
How to undo everything this research touched and return to the last known-good state.
```

## Commit Style

Follow `COMMITSTYLE.md`. For research/documentation commits:
- `sony-pdx213: bluetooth DTS research, UART timeout findings`
- `sony-pdx213: document battery PMIC gap and kernel config needs`

Include "UNTESTED" or "VERIFIED" in the commit body for any new boot image or DTS change.

## Boot Image Naming

Format: `boot-mobian-{feature}.img`

- `boot-mobian-rmtfs.img` — the baseline working image (WiFi + touch + modem + UFS)
- `boot-mobian-bt.img` — experimental with bluetooth added
- Never reuse a name for a different image without bumping a version or date suffix

The canonical working image is always `build/boot-mobian-rmtfs.img`. The `images/` directory is a graveyard of old attempts — never flash from there without verifying against documentation.
