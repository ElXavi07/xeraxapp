# Xerax Root

<div align="center">

**An automated, open-source Android rooting platform powered by Codex through the OpenAI API.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-7c3aed.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-06b6d4.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android-22c55e.svg)](https://developer.android.com/tools/releases/platform-tools)
[![Safety](https://img.shields.io/badge/Execution-Allowlisted-f59e0b.svg)](docs/architecture.md)

*Connect your device. Let Xerax inspect, plan, execute, recover, and verify.*

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

- Signed Windows companion and secure updater.
- Expanded physical-device compatibility lab.
- Root verification and stock-image recovery checkpoints.
- Reviewed Magisk, KernelSU, and APatch workflow registry.
- Server-side AI diagnostics using structured, bounded operations.
- macOS and Linux companions.
- Community-submitted device evidence and reproducible test reports.

## Contributing

Device evidence, tests, documentation, UI improvements, and defensive validation
are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
Please report security issues through [SECURITY.md](SECURITY.md), not a public
issue.

## License

Licensed under the [Apache License 2.0](LICENSE).

Xerax is not affiliated with Google, Android, Magisk, KernelSU, APatch, or any
device manufacturer. Product names are the property of their respective owners.
