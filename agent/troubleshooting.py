"""Deterministic rooting diagnostics derived from reviewed failure cases."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    code: str
    title: str
    severity: str
    scope: str
    explanation: str
    actions: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    automatic: bool = False

    def public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["actions"] = list(self.actions)
        payload["stop_conditions"] = list(self.stop_conditions)
        return payload


DIAGNOSTICS = {
    "adb_unauthorized": Diagnostic(
        code="adb_unauthorized",
        title="ADB authorization is waiting on the phone",
        severity="warning",
        scope="universal",
        explanation=(
            "The computer can see the device, but Android has not approved this USB debugging key."
        ),
        actions=(
            "Unlock the phone and accept the USB debugging prompt.",
            "If no prompt appears, revoke USB debugging authorizations and reconnect the cable.",
            "Run the device scan again after Android reports the connection as authorized.",
        ),
        stop_conditions=("Do not attempt fastboot or flashing while ADB remains unauthorized.",),
    ),
    "incremental_ota": Diagnostic(
        code="incremental_ota",
        title="The OTA contains binary patches, not a complete boot image",
        severity="stop",
        scope="universal",
        explanation=(
            "BROTLI_BSDIFF and similar operations indicate an incremental payload that needs the "
            "previous firmware image. A standalone extractor cannot safely reconstruct the target "
            "partition without that exact source."
        ),
        actions=(
            "Find a full firmware package for the exact model, region, and current build.",
            "Alternatively, use a reviewed device-specific method to read the stock partition.",
            "Discard partial or zero-byte extraction output.",
        ),
        stop_conditions=(
            "Never flash output from a failed incremental payload extraction.",
            "Never substitute an image from another build, region, or model.",
        ),
    ),
    "zero_byte_image": Diagnostic(
        code="zero_byte_image",
        title="The extracted image is empty",
        severity="stop",
        scope="universal",
        explanation="A zero-byte file is failed extraction output, not a flashable partition image.",
        actions=(
            "Delete the empty file.",
            "Return to an exact full firmware package or a reviewed partition-read method.",
        ),
        stop_conditions=("Do not upload or flash the file under any circumstances.",),
    ),
    "fastboot_fetch_unsupported": Diagnostic(
        code="fastboot_fetch_unsupported",
        title="This bootloader does not support reading the partition with fastboot",
        severity="warning",
        scope="device-dependent",
        explanation=(
            "Many production bootloaders support flashing but intentionally do not implement "
            "fastboot fetch. Repeating the command will not change that capability."
        ),
        actions=(
            "Prefer the matching full factory or recovery firmware package.",
            "Check for a reviewed profile-specific partition backup method.",
            "Preserve any known-good stock image before testing alternatives.",
        ),
        stop_conditions=(
            "Do not use a similarly named image downloaded for another device.",
            "Do not assume DSU can provide root unless an exact tested profile says it can.",
        ),
    ),
    "partition_read_denied": Diagnostic(
        code="partition_read_denied",
        title="Android denied direct access to the block partition",
        severity="warning",
        scope="universal",
        explanation=(
            "Normal Android ADB shells are sandboxed and usually cannot read boot partitions. "
            "Changing the dd path or retrying does not grant the missing privilege."
        ),
        actions=(
            "Use exact full firmware when available.",
            "Use an already-rooted recovery environment only when supported by the exact device.",
            "Use a temporary DSU/GSI partition-read workflow only from a reviewed device profile.",
        ),
        stop_conditions=(
            "Do not weaken device security or boot an unverified GSI automatically.",
            "Do not continue if the stock image cannot be tied to the current build and slot.",
        ),
    ),
    "slot_mismatch": Diagnostic(
        code="slot_mismatch",
        title="The image or partition does not match the active slot",
        severity="stop",
        scope="a-b-devices",
        explanation=(
            "A/B devices may run from slot a or b. Reading one slot and flashing another can use "
            "different firmware and cause a boot failure."
        ),
        actions=(
            "Read the current slot again immediately before backup and immediately before flashing.",
            "Use the stock image from that same slot and current build.",
        ),
        stop_conditions=("Stop if the slot changed after an OTA, reboot, or failed boot.",),
    ),
    "magisk_setup_incomplete": Diagnostic(
        code="magisk_setup_incomplete",
        title="The patched image booted but Magisk setup is incomplete",
        severity="warning",
        scope="magisk",
        explanation=(
            "A successful boot does not prove root. Magisk may require one final in-app setup and "
            "reboot before su becomes available."
        ),
        actions=(
            "Open Magisk on the device and complete any requested additional setup.",
            "Reboot once, then verify with su -c id.",
        ),
        stop_conditions=(
            "Do not report success until su returns uid=0.",
            "Do not relock the bootloader while a modified image is installed.",
        ),
    ),
    "dsu_profile_required": Diagnostic(
        code="dsu_profile_required",
        title="Temporary DSU root is not approved for this device",
        severity="stop",
        scope="profile-specific",
        explanation=(
            "DSU/GSI compatibility, dynamic-partition capacity, verified boot behavior, and adb-root "
            "support vary by device and image. The successful OnePlus 12R case is evidence for that "
            "specific build, not a universal Android recovery method."
        ),
        actions=(
            "Use full matching firmware if available.",
            "Wait for a physical-device-tested Xerax profile before attempting DSU automation.",
        ),
        stop_conditions=(
            "Do not download or boot a GSI selected by AI.",
            "Do not stage DSU without an exact profile, checksum, rollback plan, and user confirmation.",
        ),
    ),
}

SYMPTOM_PATTERNS = (
    (re.compile(r"\bunauthorized\b", re.I), "adb_unauthorized"),
    (re.compile(r"BROTLI_BSDIFF|SOURCE_BSDIFF|incremental\s+OTA", re.I), "incremental_ota"),
    (re.compile(r"\bzero[- ]byte\b|\b0\s+bytes?\b", re.I), "zero_byte_image"),
    (re.compile(r"fetch.*(?:not supported|unsupported)|did not support fetch", re.I),
     "fastboot_fetch_unsupported"),
    (re.compile(r"(?:permission denied|operation not permitted).*(?:/dev/block|by-name)|"
                r"(?:/dev/block|by-name).*(?:permission denied|operation not permitted)", re.I),
     "partition_read_denied"),
    (re.compile(r"\bslot\b.*\b(?:mismatch|changed|different)\b", re.I), "slot_mismatch"),
    (re.compile(r"\bsu\b.*(?:not found|missing|permission denied)|additional setup", re.I),
     "magisk_setup_incomplete"),
    (re.compile(r"\bDSU\b|\bGSI\b|gsi_tool", re.I), "dsu_profile_required"),
)


def diagnose_text(text: str) -> list[Diagnostic]:
    normalized = text.strip()
    if not normalized:
        return []
    codes = []
    for pattern, code in SYMPTOM_PATTERNS:
        if pattern.search(normalized) and code not in codes:
            codes.append(code)
    return [DIAGNOSTICS[code] for code in codes]


def diagnostic_by_code(code: str) -> Diagnostic | None:
    return DIAGNOSTICS.get(code)


def diagnostic_catalog() -> list[dict[str, Any]]:
    return [diagnostic.public_dict() for diagnostic in DIAGNOSTICS.values()]

