# Xerax Root

<div align="center">

**A guarded, open-source Android rooting console built for clarity, verification, and recovery.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-7c3aed.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-06b6d4.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android-22c55e.svg)](https://developer.android.com/tools/releases/platform-tools)
[![Safety](https://img.shields.io/badge/Execution-Allowlisted-f59e0b.svg)](docs/architecture.md)

*Connect. Inspect. Verify. Root with a plan.*

</div>

---

## What We Are Building

Xerax Root turns a complicated Android boot-image workflow into a focused web
console backed by a local companion application. It detects the connected device,
checks the bootloader and firmware context, validates the selected image, guides
the user through destructive confirmations, and verifies each operation before it
runs.

The long-term vision is an AI-assisted root orchestrator that can explain errors
and recommend reviewed recovery paths without giving an AI unrestricted access to
the user's shell. Device commands and boot images remain local. Executable actions
are typed, allowlisted, and checked again by the companion.

> [!IMPORTANT]
> Xerax is for devices you own or are explicitly authorized to modify. Unlocking a
> bootloader commonly erases the device and can affect security, warranty, updates,
> and app compatibility. No tool can truthfully guarantee root support for every
> Android device, firmware build, carrier, or OEM policy.

## Why Xerax

- **Website-first experience** with a clean terminal-style interface.
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

A future server-side AI layer may interpret sanitized diagnostics and select from
reviewed workflows. It will not receive boot images, serial numbers, pairing
tokens, or unrestricted command access.

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
