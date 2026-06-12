# Xerax Root architecture

## Why a companion is required

A normal webpage cannot launch a terminal, call `adb`, call `fastboot`, or freely access
USB devices. Those browser restrictions are intentional. Xerax therefore has two parts:

1. The static web console hosted at `xeraxapp.com`.
2. A signed local companion bound only to `127.0.0.1`.

The web console sends narrow, typed requests to the companion. The companion never
accepts arbitrary shell commands.

## Trust boundaries

- Device commands and uploaded boot images stay on the user's computer.
- The companion accepts browser requests only from the production Xerax origins and
  local development origins.
- Every companion launch creates a new six-digit pairing code.
- Flashing is disabled unless the user starts the companion with `--enable-flashing`.
- The flash endpoint only permits `boot` and `init_boot`, rechecks the live device,
  verifies unlock state, and requires the exact serial number.
- A versioned local manifest can match exact Android product identifiers. When a
  profile matches, the companion enforces its partition even if the browser is modified.
- Unknown devices stay in manual mode and require an additional partition confirmation.
- Uploaded images are capped at 256 MB and removed after use or after one hour.

## AI boundary

An AI service may later summarize sanitized error codes and suggest official
documentation. It must not:

- generate commands that are executed automatically;
- choose a partition;
- select firmware for a device;
- bypass unlock checks or confirmation;
- receive serial numbers, boot images, tokens, or raw device identifiers.

Root troubleshooting uses deterministic reviewed patterns before any AI
explanation. See `docs/troubleshooting.md`. In particular, DSU/GSI methods are
profile-gated because compatibility and data-loss risk vary by device.

## Compatibility

There is no truthful universal rooting procedure for every Android device. Partition
layout, anti-rollback behavior, boot image format, firmware packaging, and OEM policy
vary by device and build. The initial companion implements the common Magisk patched
`boot` / `init_boot` fastboot flow and fails closed elsewhere.

## Device profiles

`profiles/device_profiles.json` is the compatibility authority bundled into each
companion release. An entry must have a unique product identifier, a reviewed target
partition, and either `beta` or `tested` status. A profile should only be promoted to
`tested` after the complete detect, validate, flash, reboot, and root-verification flow
passes on a physical device using matching firmware.

The initial manifest is intentionally empty. Shipping guessed profiles would turn a
compatibility label into false assurance. Product entries are added as physical-device
evidence is collected.
