# Xerax Root Roadmap

Xerax aims to become the open automation and recovery layer for authorized
Android modification. This document describes the direction of the project, not
a promise that every listed feature is available today.

## Status Labels

- **Available:** implemented in the repository.
- **In development:** active design or implementation work.
- **Planned:** accepted direction that still needs design and contributors.
- **Research:** requires device evidence or technical validation.

## Milestone 1: Guarded Foundation

**Status: Available and evolving**

- Localhost-only Windows companion.
- Six-digit browser pairing.
- ADB and Fastboot device detection.
- Android boot-image validation.
- Restricted `boot` and `init_boot` flashing.
- Explicit consent and unlocked-bootloader checks.
- Exact device-profile enforcement.
- Deterministic troubleshooting rules.
- Source tests and build tooling.

## Milestone 2: Verification And Recovery

**Status: In development**

- End-to-end root verification.
- Known-good image checkpoints.
- Stock restoration after a failed operation.
- Root session audit reports with sensitive identifiers removed.
- Device health and USB stability checks.
- Recovery Package Generator.
- Bootloop Rescue Mode for reviewed device profiles.

## Milestone 3: Codex Automation

**Status: Planned**

- Server-side OpenAI Responses API integration.
- Codex-powered planning over reviewed workflow manifests.
- Structured operations instead of arbitrary shell commands.
- Sanitized diagnostic interpretation.
- Bounded retries, tool rounds, time, and API spend.
- Automatic selection among compatible recovery branches.
- Root Method Advisor for Magisk, KernelSU, and APatch.
- A terminal-only product experience rather than a general chatbot.

The agent will continue through recoverable problems, but it will stop when
firmware identity, compatibility, artifacts, or recovery conditions cannot be
verified.

## Milestone 4: Open Compatibility Network

**Status: Planned**

- Public Compatibility Registry.
- Signed and versioned workflow manifests.
- Community device-evidence submissions.
- Experimental and tested profile channels.
- Reproducible physical-device test reports.
- Firmware fingerprint and hash records.
- Manufacturer and carrier policy notes.
- Compatibility confidence based on evidence, not model guesses.

## Milestone 5: Simulation And Workflow Tooling

**Status: Planned**

- Simulation Lab using sanitized recorded sessions.
- Workflow Studio visual editor.
- Schema validation and workflow linting.
- Destructive-operation analysis.
- Recovery-path coverage reports.
- Maintainer review and signing tools.
- Regression fixtures for device-specific failures.

## Milestone 6: Root Lifecycle

**Status: Research and planned**

- One-click verified unroot.
- OTA Survival Assistant.
- Post-update root reapplication.
- Module Safety Scanner.
- Encrypted local backups.
- Module and root-method compatibility reporting.
- Stock-state verification for users returning to official software.

## Milestone 7: Platform Expansion

**Status: Planned**

- Signed Windows installer and secure updater.
- macOS companion.
- Linux companion.
- Guided and expert interfaces.
- Accessibility audits.
- Community localization.
- Technician dashboard for authorized devices.

## Community Programs

### Device Evidence Reports

Users can opt in to submit minimized reports containing only the technical facts
needed to improve compatibility. Reports must exclude serial numbers, personal
files, pairing tokens, API keys, and proprietary firmware.

### Test Bounties

Supporters will be able to sponsor testing for particular devices or firmware
builds. Results should be published whether the workflow succeeds, fails, or
reveals that the device cannot be safely supported.

### Compatibility Lab

Project funding can purchase representative physical devices and maintain a
transparent test matrix. Profiles move to `tested` only after complete physical
verification.

## How Priorities Are Chosen

Work should be prioritized using:

1. Safety and recovery impact.
2. Number of users and available device evidence.
3. Reproducibility across exact firmware builds.
4. Contributor availability.
5. Cost of obtaining and maintaining physical hardware.
6. Ability to test without making unsupported claims.

Open a
[feature proposal](https://github.com/ElXavi07/xeraxapp/issues/new?template=feature-request.yml)
or
[device support request](https://github.com/ElXavi07/xeraxapp/issues/new?template=device-support.yml)
to help shape the roadmap.
