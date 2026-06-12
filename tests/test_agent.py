import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from xerax_agent import (
    inspect_device,
    parse_adb_devices,
    parse_fastboot_devices,
    validate_image_bytes,
)
from device_profiles import load_profile_manifest, match_profile
from troubleshooting import diagnose_text, diagnostic_by_code


class ParserTests(unittest.TestCase):
    def test_parses_adb_states(self):
        output = (
            "List of devices attached\n"
            "ABC123\tdevice product:husky model:Pixel_8_Pro\n"
            "XYZ987\tunauthorized\n"
        )
        self.assertEqual(
            parse_adb_devices(output),
            [("ABC123", "device"), ("XYZ987", "unauthorized")],
        )

    def test_parses_fastboot_devices(self):
        self.assertEqual(
            parse_fastboot_devices("ABC123\tfastboot\n"),
            ["ABC123"],
        )

    def test_accepts_android_boot_image(self):
        content = b"ANDROID!" + (b"\x00" * 4096)
        result = validate_image_bytes(content, "magisk_patched.img")
        self.assertEqual(result["size"], len(content))
        self.assertFalse(result["magiskMarkerFound"])

    def test_rejects_non_image(self):
        with self.assertRaisesRegex(ValueError, "Android boot-image magic"):
            validate_image_bytes(b"not a boot image" + (b"\x00" * 4096), "bad.img")

    def test_rejects_wrong_extension(self):
        with self.assertRaisesRegex(ValueError, ".img extension"):
            validate_image_bytes(b"ANDROID!" + (b"\x00" * 4096), "boot.zip")

    @patch("xerax_agent.get_fastboot_var")
    @patch("xerax_agent.run_command")
    @patch("xerax_agent.executable")
    def test_secure_no_means_unlocked(self, mock_executable, mock_run, mock_getvar):
        mock_executable.side_effect = lambda name: name
        mock_run.return_value.stdout = "ABC123\tfastboot\n"
        mock_getvar.side_effect = [None, "no", "husky", "a", "yes", "yes"]

        device = inspect_device()

        self.assertEqual(device.mode, "fastboot")
        self.assertTrue(device.unlocked)
        self.assertEqual(device.model, "husky")

    def test_loads_and_matches_exact_profile(self):
        payload = {
            "schemaVersion": 1,
            "revision": "test.1",
            "profiles": [
                {
                    "id": "example-phone",
                    "manufacturer": "Example",
                    "displayName": "Example Phone",
                    "products": ["example_product"],
                    "partition": "init_boot",
                    "workflow": "magisk-patched-image",
                    "status": "beta",
                    "notes": "Test fixture",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            manifest = load_profile_manifest(path)

        profile = match_profile(manifest, "EXAMPLE_PRODUCT")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.partition, "init_boot")

    def test_rejects_duplicate_profile_products(self):
        payload = {
            "schemaVersion": 1,
            "revision": "test.1",
            "profiles": [
                {
                    "id": profile_id,
                    "manufacturer": "Example",
                    "displayName": profile_id,
                    "products": ["same_product"],
                    "partition": "boot",
                    "workflow": "magisk-patched-image",
                    "status": "beta",
                    "notes": "",
                }
                for profile_id in ("one", "two")
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profiles.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate product identifier"):
                load_profile_manifest(path)

    @patch("xerax_agent.run_command")
    @patch("xerax_agent.executable")
    def test_no_device_still_reports_profile_revision(self, mock_executable, mock_run):
        mock_executable.side_effect = lambda name: name
        mock_run.return_value.stdout = ""

        device = inspect_device()

        self.assertEqual(device.profile_revision, "2026-06-11.1")
        self.assertIn("No ADB or fastboot device", device.message)

    def test_incremental_ota_and_empty_image_are_both_detected(self):
        diagnostics = diagnose_text(
            "Unhandled operation type: BROTLI_BSDIFF\n"
            "Extracted init_boot.img is 0 bytes"
        )

        self.assertEqual(
            [diagnostic.code for diagnostic in diagnostics],
            ["incremental_ota", "zero_byte_image"],
        )
        self.assertTrue(all(diagnostic.severity == "stop" for diagnostic in diagnostics))

    def test_partition_permission_error_is_detected(self):
        diagnostics = diagnose_text(
            "dd: /dev/block/by-name/init_boot_b: Permission denied"
        )

        self.assertEqual([diagnostic.code for diagnostic in diagnostics],
                         ["partition_read_denied"])

    def test_dsu_guidance_is_profile_specific_and_never_automatic(self):
        diagnostic = diagnostic_by_code("dsu_profile_required")

        self.assertEqual(diagnostic.scope, "profile-specific")
        self.assertFalse(diagnostic.automatic)
        self.assertIn("exact profile", " ".join(diagnostic.stop_conditions))

    def test_unknown_troubleshooting_text_returns_no_guess(self):
        self.assertEqual(diagnose_text("mysterious vendor error 927"), [])


if __name__ == "__main__":
    unittest.main()
