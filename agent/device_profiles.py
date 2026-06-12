"""Versioned device-profile loading and exact product matching."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SCHEMA_VERSION = 1
ALLOWED_PARTITIONS = {"boot", "init_boot"}


@dataclass(frozen=True)
class DeviceProfile:
    profile_id: str
    manufacturer: str
    display_name: str
    products: tuple[str, ...]
    partition: str
    workflow: str
    status: str
    notes: str

    def public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["products"] = list(self.products)
        return payload


@dataclass(frozen=True)
class ProfileManifest:
    schema_version: int
    revision: str
    profiles: tuple[DeviceProfile, ...]


def resource_path(relative_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative_path


def load_profile_manifest(path: Path | None = None) -> ProfileManifest:
    manifest_path = path or resource_path("profiles/device_profiles.json")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to load device profiles: {error}") from error

    schema_version = payload.get("schemaVersion")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"Unsupported device-profile schema: {schema_version!r}")

    revision = payload.get("revision")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("Device-profile revision is required.")

    profiles: list[DeviceProfile] = []
    seen_ids: set[str] = set()
    seen_products: set[str] = set()
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ValueError("Device profiles must be a list.")

    for raw in raw_profiles:
        if not isinstance(raw, dict):
            raise ValueError("Each device profile must be an object.")
        profile_id = raw.get("id")
        products = raw.get("products")
        partition = raw.get("partition")
        if not isinstance(profile_id, str) or not profile_id:
            raise ValueError("Every device profile needs an id.")
        if profile_id in seen_ids:
            raise ValueError(f"Duplicate device profile id: {profile_id}")
        if (
            not isinstance(products, list)
            or not products
            or any(not isinstance(item, str) or not item.strip() for item in products)
        ):
            raise ValueError(f"Profile {profile_id} needs product identifiers.")
        normalized_products = tuple(item.strip().lower() for item in products)
        overlap = seen_products.intersection(normalized_products)
        if overlap:
            raise ValueError(f"Duplicate product identifier: {sorted(overlap)[0]}")
        if partition not in ALLOWED_PARTITIONS:
            raise ValueError(f"Profile {profile_id} has an unsupported partition.")
        if raw.get("workflow") != "magisk-patched-image":
            raise ValueError(f"Profile {profile_id} has an unsupported workflow.")
        if raw.get("status") not in {"tested", "beta"}:
            raise ValueError(f"Profile {profile_id} needs tested or beta status.")

        profile = DeviceProfile(
            profile_id=profile_id,
            manufacturer=str(raw.get("manufacturer", "")).strip(),
            display_name=str(raw.get("displayName", "")).strip(),
            products=normalized_products,
            partition=partition,
            workflow=raw["workflow"],
            status=raw["status"],
            notes=str(raw.get("notes", "")).strip(),
        )
        if not profile.manufacturer or not profile.display_name:
            raise ValueError(f"Profile {profile_id} needs manufacturer and display name.")
        profiles.append(profile)
        seen_ids.add(profile_id)
        seen_products.update(normalized_products)

    return ProfileManifest(
        schema_version=schema_version,
        revision=revision,
        profiles=tuple(profiles),
    )


def match_profile(manifest: ProfileManifest, product: str | None) -> DeviceProfile | None:
    normalized = (product or "").strip().lower()
    if not normalized:
        return None
    return next(
        (profile for profile in manifest.profiles if normalized in profile.products),
        None,
    )

