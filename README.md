# Xerax Root

<div align="center">

**An automated, open-source Android rooting platform powered by Codex through the OpenAI API.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-7c3aed.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-06b6d4.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android-22c55e.svg)](https://developer.android.com/tools/releases/platform-tools)
[![Safety](https://img.shields.io/badge/Execution-Allowlisted-f59e0b.svg)](docs/architecture.md)
[![Roadmap](https://img.shields.io/badge/Roadmap-Community_Driven-ec4899.svg)](ROADMAP.md)

*Connect your device. Let Xerax inspect, plan, execute, recover, and verify.*

[Explore the roadmap](ROADMAP.md) ·
[Join the community](COMMUNITY.md) ·
[Request a device](https://github.com/ElXavi07/xeraxapp/issues/new?template=device-support.yml) ·
[Propose a feature](https://github.com/ElXavi07/xeraxapp/issues/new?template=feature-request.yml)

</div>

---

## What We Are Building

Xerax Root is being built as an automated Android rooting orchestrator. A
Codex-powered agent, connected through the OpenAI Responses API, will inspect the
device state, choose the best compatible reviewed workflow, guide required
physical confirmations, diagnose recoverable failures, and continue until root is
independently verified or a safety boundary requires it to stop.

The customer sees one focused terminal instead of a general-purpose chatbot.
Xerax handles the workflow from compatibility scanning through bootloader
unlocking, image preparation, flashing, reboot, recovery, and final root
verification. The local companion performs the actual ADB and Fastboot operations
on the user's computer.

Codex does not receive unrestricted shell access. Device commands are represented
as structured operations selected from reviewed workflows, then validated by the
server and local companion before execution. Device commands and boot images stay
local.

> [!IMPORTANT]
> Xerax is for devices you own or are explicitly authorized to modify. Unlocking a
> bootloader commonly erases the device and can affect security, warranty, updates,
> and app compatibility. No tool can truthfully guarantee root support for every
> Android device, firmware build, carrier, or OEM policy.

## Why Xerax

- **Website-first experience** with a clean terminal-style interface.
- **Codex-powered automation** through the server-side OpenAI Responses API.
- **End-to-end orchestration** from device detection to verified root.
- **Adaptive troubleshooting** that can continue through recoverable failures.
- **Local execution** through a companion bound only to `127.0.0.1`.
- **No arbitrary shell endpoint** and no model-generated command execution.
- **Exact-device profiles** for reviewed partition and workflow decisions.
- **Image validation and live checks** before a flash can begin.
- **Explicit consent gates** for data loss and high-risk operations.
- **Recovery-first design** that fails closed when compatibility is uncertain.
- **Open development** so workflows and trust boundaries can be reviewed.

## How It Works

```text
Xerax web console
        |
        | paired, typed localhost requests
        v
Xerax Root Companion
        |
        | allowlisted adb / fastboot operations
        v
Authorized Android device
```

The planned server-side Codex agent receives sanitized diagnostics and selects
from reviewed workflows through the OpenAI API. It will not receive boot images,
serial numbers, pairing tokens, or unrestricted command access.

## Current Status

Xerax currently supports the guarded foundation of a common Magisk patched
`boot` / `init_boot` fastboot workflow:

- Detect one ADB or fastboot device.
- Record product, build, slot, and bootloader details.
- Match exact device profiles from a versioned manifest.
- Validate Android boot images and reject invalid uploads.
- Restrict flashing to `boot` and `init_boot`.
- Require explicit confirmation and an unlocked bootloader.
- Provide reviewed troubleshooting guidance without guessing.

The production device manifest is intentionally conservative. A profile becomes
`tested` only after its complete detect, validate, flash, reboot, and root
verification workflow succeeds on matching physical hardware and firmware.

The complete Codex API automation layer described above is under active
development and is not yet included in the current release.

## The Experience We Are Building

```text
ROOT TERMINAL

> Pixel 8 detected
> Firmware and partition layout verified
> Recommended method: Magisk
> Recovery checkpoint prepared
> Bootloader confirmation required on device
> Patched image verified and flashed
> Device rebooted successfully
> Root access verified

STATUS: ROOTED
RECOVERY: READY
```

The finished experience should feel simple without hiding what matters. Xerax
will explain risk once, request physical confirmation when Android requires it,
show every important transition, and keep the technical logs available for users
who want them.

## Feature Universe

### Automated Rooting

- **One-terminal root:** detect, plan, unlock, patch, flash, reboot, and verify.
- **Root Method Advisor:** recommend Magisk, KernelSU, or APatch using exact
  device, kernel, firmware, and user priorities.
- **Codex Recovery Agent:** interpret sanitized failures and choose the next
  reviewed recovery branch.
- **Bootloop Rescue Mode:** recognize failed boots and restore a known-good
  image when a verified recovery path exists.
- **Root Verification Report:** prove the active slot, root method, patched
  partition, manager state, and recovery readiness.

### Updates And Recovery

- **One-click unroot:** restore reviewed stock partitions and verify the result.
- **OTA Survival Assistant:** prepare for supported updates and safely reapply
  root afterward.
- **Verified Firmware Finder:** locate approved official artifacts and validate
  checksums before use.
- **Recovery Package Generator:** prepare local stock images, hashes, device
  context, and recovery instructions before modification begins.
- **Encrypted Local Backups:** protect recovery checkpoints without uploading
  private device files.

### Safety And Privacy

- **Device Health Check:** inspect battery, USB stability, drivers, storage,
  bootloader state, partition layout, slots, and anti-rollback signals.
- **Module Safety Scanner:** analyze community root modules and flag dangerous
  permissions or suspicious behavior before installation.
- **Private Mode:** send only minimized, sanitized diagnostics to the API while
  boot images and device files remain local.
- **Signed Workflow Manifests:** make reviewed actions reproducible and
  tamper-evident.
- **Emergency Stop:** cancel safely and present the best available recovery
  checkpoint.

### Every Kind Of User

- **Guided Mode:** plain-language instructions and clear phone-side actions.
- **Expert Mode:** full logs, workflow visualization, hashes, partition state,
  and approved manual controls.
- **Technician Dashboard:** authorized device sessions, reports, reusable
  workflows, and fleet-level compatibility visibility.
- **Windows, macOS, and Linux companions.**
- **Accessible and localized interfaces** built with community translators.

## The Open Compatibility Network

Xerax will not hide device knowledge inside a private prompt. The community can
build a public compatibility network containing:

- Exact device and firmware profiles
- Tested root methods and partition targets
- Sanitized success and failure evidence
- Reproducible recovery procedures
- Firmware hashes and trusted-source metadata
- Compatibility confidence and test history
- Community translations and manufacturer-specific documentation

Every workflow moves through an evidence-based pipeline:

```text
Community submission
        |
        v
Automated schema and safety validation
        |
        v
Maintainer review
        |
        v
Experimental profile
        |
        v
Matching physical-device verification
        |
        v
Tested community profile
```

No popularity contest can turn an unverified flashing procedure into a trusted
profile. Evidence does.

## Community Projects We Want To Build

1. **Xerax Compatibility Registry**

   A searchable public database of devices, builds, methods, confidence,
   successful tests, known limitations, and recovery paths.

2. **Xerax Simulation Lab**

   Replay sanitized ADB and Fastboot sessions so contributors can test parsers,
   workflows, and recovery logic without risking a physical device.

3. **Workflow Studio**

   A visual editor for producing typed, reviewable workflows instead of sharing
   fragile shell scripts.

4. **Device Evidence Reports**

   Let users opt in to contribute minimized compatibility evidence after a
   successful or safely recovered session.

5. **Community Test Bounties**

   Allow supporters to fund physical testing for requested devices and firmware
   versions, with public results.

6. **Open Recovery Library**

   Build a reviewed collection of stock restoration and bootloop recovery paths
   tied to exact device evidence.

## Run Locally

Requirements:

- Python 3.10 or newer
- [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
  (`adb` and `fastboot`) on `PATH`
- A Chromium-based browser

Start the web console:

```powershell
python -m http.server 8000 --directory web
```

In another terminal, start the companion in inspection-only mode:

```powershell
python agent/xerax_agent.py
```

Open `http://127.0.0.1:8000`, enter the six-digit pairing code, and connect.

Flashing is disabled by default. For development with an authorized test device:

```powershell
python agent/xerax_agent.py --enable-flashing
```

On Windows, `companion\start-xerax.cmd` performs the same launch and verifies that
the required commands are available.

## Build And Test

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

Build the Windows companion with PyInstaller:

```powershell
.\companion\build.ps1 -Clean
```

Public executables must be code-signed. Android Platform Tools are not
redistributed; users obtain them from Google and accept Google's SDK license.

Create the static `/root/` deployment bundle:

```powershell
.\companion\deploy.ps1
```

See [the architecture](docs/architecture.md),
[deployment guide](docs/deployment.md), and
[troubleshooting rules](docs/troubleshooting.md) for the full design.

## Roadmap

The roadmap is organized around public milestones:

- **Foundation:** local companion, paired terminal, strict validation, and tests.
- **Verification:** exact profiles, recovery checkpoints, and root proof.
- **Automation:** Codex through the OpenAI API selecting reviewed workflows.
- **Community:** compatibility registry, evidence reports, and simulation lab.
- **Expansion:** KernelSU, APatch, OTA assistance, unroot, macOS, and Linux.

See [ROADMAP.md](ROADMAP.md) for the full feature map, status labels, and the
projects open to contributors.

## Contributing

Device evidence, tests, documentation, UI improvements, and defensive validation
are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
Please report security issues through [SECURITY.md](SECURITY.md), not a public
issue.

You do not need to be an Android internals expert. The project needs designers,
technical writers, translators, testers, security reviewers, Python developers,
frontend developers, and people willing to document real devices carefully.

## Help Build It

The fastest ways to support Xerax today:

- Star the repository so more Android builders discover it.
- Watch releases and roadmap discussions.
- Request support for a specific device and firmware.
- Contribute sanitized physical-device evidence.
- Improve documentation, translations, tests, or interface accessibility.
- Review workflows and security boundaries.
- Share the project with Android development and modification communities.

Future sponsorship will fund physical test devices, Windows code signing,
infrastructure, OpenAI API usage, firmware research, and independent security
audits. Funding goals and spending should remain visible to the community.

Read [COMMUNITY.md](COMMUNITY.md) to find a contribution path that fits your
skills.

> **Open workflows. Local execution. Community-verified compatibility.
> Codex-powered automation.**

## License

Licensed under the [Apache License 2.0](LICENSE).

Xerax is not affiliated with Google, Android, Magisk, KernelSU, APatch, or any
device manufacturer. Product names are the property of their respective owners.
