# 🎬 video-autopilot-kit

> **A Windows-first maintained fork that turns video-production methodology, ffmpeg automation, CapCut-assisted workflows, and mechanical QA gates into a local toolkit you can adapt with your own data.**

[繁體中文](README.md)

This repository is a fork of [`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit) and keeps the upstream MIT license and Git history. Upstream provides the core automation framework and knowledge base; this fork focuses on making it easier to develop, validate, and use on **Windows 11 + PowerShell**.

## What does this fork add?

Compared with the shared ancestor, this maintained line adds or strengthens:

- **Windows-first development and validation** with a reproducible venv, a canonical PowerShell gate, and Windows-specific regression tests.
- **Path 1 desktop workbench** using Tkinter while keeping editing rules in the existing Programmatic core.
- **Portable Windows EXE** built with PyInstaller and capable of bundling `ffmpeg`, `ffprobe`, NumPy, and Pillow; missing required dependencies fail closed.
- **Windows + Ubuntu CI**: Windows runs the full development gate plus EXE build/smoke tests, while Ubuntu provides cross-platform evidence.
- **CodeQL, Dependabot, and upstream tracking** so upstream changes are reviewed individually instead of blindly overwriting fork fixes.
- **Windows reliability fixes** around CapCut atomic writes, process shutdown, UTF-8/CJK subprocess handling, and optimized-mode guards.

See [`FORK.md`](FORK.md) for the fork boundary and [`docs/UPSTREAM.md`](docs/UPSTREAM.md) for upstream-review policy.

## Which path should I use?

| Need | Recommended path |
|---|---|
| macOS / Linux, no GUI, pure-code automation | **Path 1 Programmatic** |
| Windows and a desktop workbench | **Path 1 GUI** |
| CapCut effects, styled text, or existing templates | **Path 2 CapCut-assisted** |
| A quick proof without real media | `examples/` demos |

> The CapCut-assisted path is **version-sensitive**. Check [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before relying on it.

## See it run in 60 seconds

You can try self-contained examples without private data or real footage:

```bash
python examples/01_vertical_short.py
python examples/04_shorts_gate.py
python examples/05_interview_plan.py
python examples/06_teardown.py
```

- `01`: synthesized media → a 1080×1920 vertical short.
- `04`: Shorts gate that blocks a bad cut and accepts the corrected plan.
- `05`: interview gate that blocks unsourced guest claims before recording.
- `06`: competitor-rhythm teardown and comparable metrics.

Python **3.9+** is required. Some pure-Python gates need no ffmpeg; media-generation workflows require `ffmpeg` / `ffprobe`. See [`examples/README.md`](examples/README.md) for the full set.

## Windows Path 1 GUI

After creating the development environment:

```powershell
.venv\Scripts\python path1_gui.py
```

The desktop workbench covers the main Programmatic workflows:

- Shorts `scan → edit plan → build + QA`
- competitor-rhythm measurement
- delivery QA
- screen-recording cleanup
- ffmpeg / ffprobe / NumPy / Pillow dependency checks

Long-running media jobs execute in the background. Media, plans, and outputs stay in the local folders selected by the user.

### Build the portable EXE

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python build_exe.py
# dist\video-autopilot-path1.exe
```

The build validates required dependencies. For the complete GUI, packaging, and third-party license boundaries, read:

- [`docs/PATH1_GUI.md`](docs/PATH1_GUI.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

## Core capabilities

This is not a single "auto-edit" script. It is a set of composable workflows and gates:

- **Teaching / long-form video**: script, planning, delivery QA, and reusable long-form modules.
- **Vertical Shorts / Reels-style video**: scan, plan, build, platform-aware gates, and QA.
- **Online interviews**: invitation, guest research, planning documents, and source checks.
- **Competitor teardown**: cut rhythm, sentence changes, loudness, and other measurements; OCR is optional.
- **Channel operations**: tracking and system-health utilities.
- **CapCut helpers**: Windows-first draft, process, and post-export helpers.

The deeper methodology and knowledge base continue to evolve upstream. This fork does not repackage upstream research as original SanHsien work.

## Data and privacy boundaries

This repository **should not contain anyone's private channel data or media**:

- `profiles/`, `config.py`, and personal settings remain local and are ignored by Git.
- Do not commit video, audio, transcripts, CapCut drafts, API keys, cookies, or account data.
- When `knowledge/` names third-party creators or channels, use public information only and follow **citation-first: no source link, no number**.
- KPI thresholds, voice vocabularies, and community fields should be blank templates, placeholders, or explicitly labelled examples.
- OCR confidence is not evidence that a product name, price, material, or quantity is true; high-risk captions still require human or source verification.
- If an external transcription or AI service is used, that service's own policy governs its data handling; this repository does not make privacy promises on behalf of third parties.

## Development and validation

Primary validation environment: **Windows 11 + PowerShell**.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-dev.txt
pwsh -NoProfile -File tools\dev_check.ps1
```

CI additionally verifies:

- Ubuntu / Python 3.9: compile, Ruff, pytest, and system health.
- Windows / Python 3.14: the canonical full development gate.
- Windows: a real `video-autopilot-path1.exe` build, followed by GUI startup and bundled `ffmpeg` / `ffprobe` / NumPy / Pillow checks.
- CodeQL: Python security analysis.

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for development details.

## Documentation map

| Purpose | Document |
|---|---|
| First-time setup | [`SETUP.md`](SETUP.md) |
| Troubleshooting / CapCut compatibility | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| Fork differences | [`FORK.md`](FORK.md) |
| Upstream review | [`docs/UPSTREAM.md`](docs/UPSTREAM.md) |
| Development and validation | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) |
| Path 1 GUI / EXE | [`docs/PATH1_GUI.md`](docs/PATH1_GUI.md) |
| External integrations | [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) |
| Fork-specific decisions | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| Version history | [`CHANGELOG.md`](CHANGELOG.md) |
| Latest repository review | [`REPO_REVIEW.md`](REPO_REVIEW.md) |

## Upstream and license

- Upstream: [`Hao0321/video-autopilot-kit`](https://github.com/Hao0321/video-autopilot-kit)
- Maintained fork: [`SanHsien/video-autopilot-kit`](https://github.com/SanHsien/video-autopilot-kit)
- License: MIT

Upstream may be ahead of this fork. Run `python tools/check_upstream_updates.py` and review changes individually before merging or cherry-picking. The value of this fork is **Windows-first adoption, validation, and maintained divergence**, not relabelling upstream work.
