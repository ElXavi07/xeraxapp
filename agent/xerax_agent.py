#!/usr/bin/env python3
"""Local USB companion for the Xerax Root web console."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from device_profiles import (
    ALLOWED_PARTITIONS,
    DeviceProfile,
    ProfileManifest,
    load_profile_manifest,
    match_profile,
)
from troubleshooting import diagnostic_by_code, diagnostic_catalog, diagnose_text

VERSION = "0.3.0"
HOST = "127.0.0.1"
PORT = 47721
MAX_IMAGE_BYTES = 256 * 1024 * 1024
ALLOWED_ORIGINS = {
    "https://xeraxapp.com",
    "https://www.xeraxapp.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}


@dataclass
class Device:
    mode: str | None = None
    serial: str | None = None
    model: str | None = None
    product: str | None = None
    build_fingerprint: str | None = None
    ota_build: str | None = None
    sdk: str | None = None
    current_slot: str | None = None
    flash_locked: bool | None = None
    verified_boot_state: str | None = None
    has_boot: bool | None = None
    has_init_boot: bool | None = None
    unlocked: bool | None = None
    message: str | None = None
    profile: dict[str, Any] | None = None
    profile_revision: str | None = None


@dataclass
class AgentConfig:
    token: str
    enable_flashing: bool
    upload_dir: Path
    manifest: ProfileManifest


def first_output_line(result: subprocess.CompletedProcess[str]) -> str | None:
    combined = f"{result.stdout}\n{result.stderr}".strip()
    return combined.splitlines()[0].strip() if combined else None


def run_command(command: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def executable(name: str) -> str | None:
    executable_name = f"{name}.exe" if os.name == "nt" else name
    candidates = [
        Path(getattr(sys, "_MEIPASS", "")) / "platform-tools" / executable_name,
        Path(sys.executable).resolve().parent / "platform-tools" / executable_name,
        Path(__file__).resolve().parents[1] / "companion" / "platform-tools" / executable_name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def platform_tools_status() -> dict[str, Any]:
    adb = executable("adb")
    fastboot = executable("fastboot")
    return {
        "ready": bool(adb and fastboot),
        "adb": {
            "available": bool(adb),
            "version": first_output_line(run_command([adb, "version"])) if adb else None,
        },
        "fastboot": {
            "available": bool(fastboot),
            "version": first_output_line(run_command([fastboot, "--version"])) if fastboot else None,
        },
    }


def parse_adb_devices(output: str) -> list[tuple[str, str]]:
    devices: list[tuple[str, str]] = []
    for line in output.splitlines()[1:]:
        fields = line.strip().split()
        if len(fields) >= 2:
            devices.append((fields[0], fields[1]))
    return devices


def parse_fastboot_devices(output: str) -> list[str]:
    devices = []
    for line in output.splitlines():
        fields = line.strip().split()
        if fields:
            devices.append(fields[0])
    return devices


def get_fastboot_var(fastboot: str, serial: str, name: str) -> str | None:
    result = run_command([fastboot, "-s", serial, "getvar", name])
    combined = f"{result.stdout}\n{result.stderr}"
    match = re.search(rf"(?:\(bootloader\)\s*)?{re.escape(name)}:\s*(\S+)", combined, re.I)
    return match.group(1).strip() if match else None


def fastboot_yes_no(fastboot: str, serial: str, name: str) -> bool | None:
    value = get_fastboot_var(fastboot, serial, name)
    if value is None:
        return None
    if value.lower() in {"yes", "true", "1"}:
        return True
    if value.lower() in {"no", "false", "0"}:
        return False
    return None


def adb_property(adb: str, serial: str, name: str) -> str | None:
    result = run_command([adb, "-s", serial, "shell", "getprop", name])
    value = result.stdout.strip()
    return value or None


def property_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    if value.lower() in {"1", "yes", "true"}:
        return True
    if value.lower() in {"0", "no", "false"}:
        return False
    return None


def profile_payload(profile: DeviceProfile | None) -> dict[str, Any] | None:
    return profile.public_dict() if profile else None


def inspect_device(manifest: ProfileManifest | None = None) -> Device:
    active_manifest = manifest or load_profile_manifest()
    fastboot = executable("fastboot")
    adb = executable("adb")

    if fastboot:
        result = run_command([fastboot, "devices"])
        fastboot_devices = parse_fastboot_devices(result.stdout)
        if len(fastboot_devices) > 1:
            return Device(
                message="Multiple fastboot devices found. Connect exactly one.",
                profile_revision=active_manifest.revision,
            )
        if len(fastboot_devices) == 1:
            serial = fastboot_devices[0]
            unlocked_value = get_fastboot_var(fastboot, serial, "unlocked")
            if unlocked_value is None:
                unlocked_value = get_fastboot_var(fastboot, serial, "secure")
                if unlocked_value is None:
                    unlocked = None
                else:
                    unlocked = unlocked_value.lower() in {"no", "false", "0"}
            else:
                unlocked = unlocked_value.lower() in {"yes", "true", "1"}
            product = get_fastboot_var(fastboot, serial, "product")
            profile = match_profile(active_manifest, product)
            return Device(
                mode="fastboot",
                serial=serial,
                model=product or "Unknown fastboot product",
                product=product,
                current_slot=get_fastboot_var(fastboot, serial, "current-slot"),
                has_boot=fastboot_yes_no(fastboot, serial, "has-slot:boot"),
                has_init_boot=fastboot_yes_no(fastboot, serial, "has-slot:init_boot"),
                unlocked=unlocked,
                message=None if unlocked is not None else "Unlock state could not be verified.",
                profile=profile_payload(profile),
                profile_revision=active_manifest.revision,
            )

    if adb:
        result = run_command([adb, "devices"])
        adb_devices = parse_adb_devices(result.stdout)
        usable = [(serial, status) for serial, status in adb_devices if status == "device"]
        if len(usable) > 1:
            return Device(
                message="Multiple ADB devices found. Connect exactly one.",
                profile_revision=active_manifest.revision,
            )
        if len(usable) == 1:
            serial = usable[0][0]
            model = adb_property(adb, serial, "ro.product.model") or "Unknown Android device"
            product = adb_property(adb, serial, "ro.product.device")
            profile = match_profile(active_manifest, product)
            return Device(
                mode="adb",
                serial=serial,
                model=model,
                product=product,
                build_fingerprint=adb_property(adb, serial, "ro.build.fingerprint"),
                ota_build=(
                    adb_property(adb, serial, "ro.build.version.ota")
                    or adb_property(adb, serial, "ro.build.display.full_id")
                ),
                sdk=adb_property(adb, serial, "ro.build.version.sdk"),
                current_slot=(
                    adb_property(adb, serial, "ro.boot.slot_suffix") or ""
                ).lstrip("_") or None,
                flash_locked=property_bool(
                    adb_property(adb, serial, "ro.boot.flash.locked")
                ),
                verified_boot_state=adb_property(
                    adb, serial, "ro.boot.verifiedbootstate"
                ),
                unlocked=None,
                message="Reboot to the bootloader to verify unlock state.",
                profile=profile_payload(profile),
                profile_revision=active_manifest.revision,
            )
        if adb_devices:
            serial, status = adb_devices[0]
            return Device(
                mode="adb",
                serial=serial,
                unlocked=None,
                message=f"ADB device is {status}. Approve USB debugging on the device.",
                profile_revision=active_manifest.revision,
            )

    missing = []
    if not adb:
        missing.append("adb")
    if not fastboot:
        missing.append("fastboot")
    if missing:
        return Device(
            message=f"Missing Android platform tools: {', '.join(missing)}.",
            profile_revision=active_manifest.revision,
        )
    return Device(
        message="No ADB or fastboot device found.",
        profile_revision=active_manifest.revision,
    )


def validate_image_bytes(content: bytes, filename: str) -> dict[str, Any]:
    if not filename.lower().endswith(".img"):
        raise ValueError("The selected file must use the .img extension.")
    if len(content) < 4096:
        raise ValueError("The image is too small to be an Android boot image.")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("The image exceeds the 256 MB safety limit.")

    has_boot_magic = content.startswith(b"ANDROID!")
    has_vendor_magic = content.startswith(b"VNDRBOOT")
    has_magisk_marker = b"MAGISK" in content[: 16 * 1024 * 1024].upper()
    if not (has_boot_magic or has_vendor_magic):
        raise ValueError("Android boot-image magic was not found.")

    return {
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "magiskMarkerFound": has_magisk_marker,
    }


class XeraxHandler(BaseHTTPRequestHandler):
    server_version = "XeraxCompanion"

    @property
    def config(self) -> AgentConfig:
        return self.server.config  # type: ignore[attr-defined]

    def log_message(self, format_string: str, *args: Any) -> None:
        print(f"[http] {self.client_address[0]} {format_string % args}")

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin in ALLOWED_ORIGINS

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Xerax-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _authorized(self) -> bool:
        if not self._origin_allowed():
            self._json(HTTPStatus.FORBIDDEN, {"error": "This website origin is not allowed."})
            return False
        supplied = self.headers.get("X-Xerax-Token", "")
        if not secrets.compare_digest(supplied, self.config.token):
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "Pairing code is incorrect."})
            return False
        return True

    def _read_body(self, maximum: int) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length.") from error
        if length <= 0:
            raise ValueError("Request body is empty.")
        if length > maximum:
            raise ValueError("Request body exceeds the allowed size.")
        return self.rfile.read(length)

    def do_OPTIONS(self) -> None:
        if not self._origin_allowed():
            self._json(HTTPStatus.FORBIDDEN, {"error": "This website origin is not allowed."})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if not self._authorized():
            return
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "version": VERSION,
                    "flashingEnabled": self.config.enable_flashing,
                    "profileRevision": self.config.manifest.revision,
                    "profileCount": len(self.config.manifest.profiles),
                    "platformTools": platform_tools_status(),
                },
            )
            return
        if path == "/api/device":
            self._json(
                HTTPStatus.OK,
                {"device": asdict(inspect_device(self.config.manifest))},
            )
            return
        if path == "/api/profiles":
            self._json(
                HTTPStatus.OK,
                {
                    "revision": self.config.manifest.revision,
                    "profiles": [
                        profile.public_dict() for profile in self.config.manifest.profiles
                    ],
                },
            )
            return
        if path == "/api/troubleshooting":
            self._json(HTTPStatus.OK, {"diagnostics": diagnostic_catalog()})
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def do_POST(self) -> None:
        if not self._authorized():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/image":
            self._upload_image(parse_qs(parsed.query))
            return
        if parsed.path == "/api/flash":
            self._flash_image()
            return
        if parsed.path == "/api/diagnose":
            self._diagnose()
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def _diagnose(self) -> None:
        try:
            payload = json.loads(self._read_body(16 * 1024))
        except (ValueError, json.JSONDecodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid request: {error}"})
            return

        code = str(payload.get("code", "")).strip()
        text = str(payload.get("text", "")).strip()
        diagnostics = []
        if code:
            diagnostic = diagnostic_by_code(code)
            if not diagnostic:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "Unknown troubleshooting code."})
                return
            diagnostics.append(diagnostic)
        if text:
            for diagnostic in diagnose_text(text):
                if diagnostic.code not in {item.code for item in diagnostics}:
                    diagnostics.append(diagnostic)
        self._json(
            HTTPStatus.OK,
            {
                "diagnostics": [diagnostic.public_dict() for diagnostic in diagnostics],
                "aiExecutionAllowed": False,
            },
        )

    def _upload_image(self, query: dict[str, list[str]]) -> None:
        filename = Path(query.get("filename", ["patched.img"])[0]).name
        try:
            content = self._read_body(MAX_IMAGE_BYTES)
            details = validate_image_bytes(content, filename)
        except ValueError as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        upload_id = secrets.token_urlsafe(18)
        destination = self.config.upload_dir / f"{upload_id}.img"
        destination.write_bytes(content)
        metadata = {
            "filename": filename,
            "created": int(time.time()),
            **details,
        }
        destination.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
        marker = (
            "Magisk marker found."
            if details["magiskMarkerFound"]
            else "Boot image is structurally valid; a Magisk marker was not detectable."
        )
        self._json(
            HTTPStatus.OK,
            {
                "uploadId": upload_id,
                "sha256": details["sha256"],
                "message": f"{marker} SHA-256: {details['sha256'][:16]}...",
            },
        )

    def _flash_image(self) -> None:
        try:
            payload = json.loads(self._read_body(32 * 1024))
        except (ValueError, json.JSONDecodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid request: {error}"})
            return

        if not self.config.enable_flashing:
            self._json(
                HTTPStatus.FORBIDDEN,
                {"error": "Flashing is disabled in the companion. Use --enable-flashing."},
            )
            return

        upload_id = str(payload.get("uploadId", ""))
        serial = str(payload.get("serial", ""))
        partition = str(payload.get("partition", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]{10,64}", upload_id):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid upload identifier."})
            return
        if partition not in ALLOWED_PARTITIONS:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Unsupported target partition."})
            return
        if payload.get("backupConfirmed") is not True:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Backup confirmation is required."})
            return
        if payload.get("patchedConfirmed") is not True:
            self._json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Confirmation that Magisk patched the image is required."},
            )
            return

        device = inspect_device(self.config.manifest)
        if device.mode != "fastboot" or device.unlocked is not True:
            self._json(
                HTTPStatus.CONFLICT,
                {"error": "A verified unlocked fastboot device is required."},
            )
            return
        if not serial or not secrets.compare_digest(serial, device.serial or ""):
            self._json(HTTPStatus.CONFLICT, {"error": "Device serial confirmation does not match."})
            return
        requested_profile_id = str(payload.get("profileId", ""))
        if device.profile:
            expected_profile_id = str(device.profile["profile_id"])
            expected_partition = str(device.profile["partition"])
            if not secrets.compare_digest(requested_profile_id, expected_profile_id):
                self._json(
                    HTTPStatus.CONFLICT,
                    {"error": "The confirmed device profile does not match the live device."},
                )
                return
            if partition != expected_partition:
                self._json(
                    HTTPStatus.CONFLICT,
                    {"error": f"This device profile requires the {expected_partition} partition."},
                )
                return
        elif requested_profile_id:
            self._json(
                HTTPStatus.CONFLICT,
                {"error": "No exact profile matches the live device."},
            )
            return

        image = self.config.upload_dir / f"{upload_id}.img"
        if not image.is_file():
            self._json(HTTPStatus.NOT_FOUND, {"error": "Validated image was not found."})
            return

        fastboot = executable("fastboot")
        if not fastboot:
            self._json(HTTPStatus.CONFLICT, {"error": "fastboot is no longer available."})
            return

        command = [fastboot, "-s", serial, "flash", partition, str(image)]
        result = run_command(command, timeout=180)
        safe_command = f"fastboot -s {serial} flash {partition} <validated-image>"
        output = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode != 0:
            self._json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Flash failed. Command: {safe_command}\n{output[-4000:]}"},
            )
            return

        reboot = run_command([fastboot, "-s", serial, "reboot"], timeout=30)
        if reboot.returncode != 0:
            self._json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"Image flashed, but reboot failed: {reboot.stderr.strip()}"},
            )
            return

        image.unlink(missing_ok=True)
        image.with_suffix(".json").unlink(missing_ok=True)
        self._json(
            HTTPStatus.OK,
            {
                "status": "complete",
                "log": [
                    f"Executed: {safe_command}",
                    output[-2000:],
                    f"Executed: fastboot -s {serial} reboot",
                ],
            },
        )


class XeraxServer(ThreadingHTTPServer):
    config: AgentConfig


def remove_stale_uploads(upload_dir: Path) -> None:
    cutoff = time.time() - 60 * 60
    for path in upload_dir.glob("*"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="Xerax Root local USB companion")
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument(
        "--enable-flashing",
        action="store_true",
        help="Allow confirmed fastboot flash operations.",
    )
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    token = f"{secrets.randbelow(1_000_000):06d}"
    upload_dir = Path(tempfile.gettempdir()) / "xerax-root-uploads"
    upload_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    remove_stale_uploads(upload_dir)
    try:
        manifest = load_profile_manifest()
    except ValueError as error:
        parser.error(str(error))

    server = XeraxServer((HOST, args.port), XeraxHandler)
    server.config = AgentConfig(
        token=token,
        enable_flashing=args.enable_flashing,
        upload_dir=upload_dir,
        manifest=manifest,
    )

    print("")
    print("Xerax Root companion")
    print("====================")
    print(f"Pairing code: {token}")
    print(f"Listening on: http://{HOST}:{args.port}")
    print(f"Flashing: {'ENABLED' if args.enable_flashing else 'disabled'}")
    print(f"Device profiles: {len(manifest.profiles)} ({manifest.revision})")
    print("Press Ctrl+C to stop. Keep this code private.")
    print("")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping companion.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
