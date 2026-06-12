# Rooting a OnePlus 12R When the Standard Firmware-Patching Path Fails

## Goal

Root a user-owned OnePlus 12R safely, without guessing or flashing mismatched boot images.

## Device

```text
OnePlus 12R NA
Model: CPH2611
Final build: CPH2611_11.F.29_2290_202604031213
OxygenOS: 16.0.5.701(EX01)
Active slot: b
Root method: Magisk patched init_boot
Final result: root confirmed with su -c id
```

## Core Principle

Never flash a random `init_boot.img`. Always use the image from the exact current build and active slot, or pull it from the device itself.

## Process

### 1. Establish ADB/Fastboot

Install Android Platform Tools and verify:

```bash
adb devices
fastboot devices
```

If ADB shows `unauthorized`, have the user unlock the phone and accept the USB debugging prompt.

### 2. Confirm Device State

Collect:

```bash
adb shell getprop ro.build.version.ota
adb shell getprop ro.build.display.full_id
adb shell getprop ro.boot.slot_suffix
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.verifiedbootstate
```

### 3. Unlock Bootloader

Only after warning the user that this wipes the phone:

```bash
adb reboot bootloader
fastboot flashing unlock
```

Confirm on the phone.

### 4. Update Before Rooting

If an official OTA is pending, install it before rooting. Root should be built for the final OS version the user intends to run.

In this case the phone updated to:

```text
CPH2611_11.F.29_2290_202604031213
```

### 5. Install Magisk

Install the Magisk APK:

```bash
adb install -r Magisk-v30.7.apk
```

### 6. Initial Problem

The normal rooting path requires stock `init_boot.img`.

The available OTA ZIP was:

```text
85199d5891e91fa971b95150a437e5fa8494380d.zip
```

It contained `payload.bin`, but it was an incremental OTA. Payload extraction failed with:

```text
Unhandled operation type: BROTLI_BSDIFF
```

That means the OTA did not contain a complete `init_boot` image. It only contained a binary patch requiring the previous source image.

Conclusion:

Do not flash anything from this OTA. The extracted `init_boot.img` was zero bytes and unusable.

### 7. Try Safe Alternatives

Fastboot fetch was attempted but the device did not support pulling the partition:

```bash
fastboot fetch init_boot_b init_boot_b.img
```

Result:

```text
Device did not support fetch.
```

Reading the partition from normal Android also failed:

```bash
adb shell dd if=/dev/block/by-name/init_boot_b of=/sdcard/init_boot_b.img
```

Result:

```text
Permission denied.
```

### 8. Use DSU/GSI Temporary Root ADB

Since the phone was bootloader-unlocked, use Android Dynamic System Update to boot a temporary GSI that allows `adb root`.

Several GSIs were tested. The working one was:

```text
TrebleDroid Android 16 ARM64 vanilla GSI
system-td-arm64-vanilla.img.xz
```

Staged through DSU, then enabled for one boot:

```bash
adb shell gsi_tool enable -s
adb reboot
```

After booting into the temporary GSI:

```bash
adb root
adb shell id
```

Expected:

```text
uid=0(root)
```

### 9. Pull Exact Stock init_boot From Device

The active slot was `b`, so pull `init_boot_b`:

```bash
adb shell dd if=/dev/block/by-name/init_boot_b of=/sdcard/init_boot_b_F29.img bs=4096
adb pull /sdcard/init_boot_b_F29.img
```

Verify size:

```text
8388608 bytes
```

This is the exact stock image for the current build and slot.

### 10. Reboot Back To OxygenOS

```bash
adb reboot
```

Confirm:

```bash
adb shell getprop ro.build.version.ota
adb shell getprop ro.boot.slot_suffix
```

### 11. Patch With Magisk

Patch the pulled `init_boot` image using Magisk.

Either use the Magisk app:

```text
Magisk > Install > Select and Patch a File > init_boot_b_F29.img
```

Or use Magisk's `boot_patch.sh` extracted from the Magisk APK.

The successful patched image was:

```text
magisk_patched_init_boot_b_F29.img
```

### 12. Flash Patched init_boot To Active Slot

Reboot to fastboot:

```bash
adb reboot bootloader
```

Confirm slot:

```bash
fastboot getvar current-slot
```

Flash only the active slot:

```bash
fastboot flash init_boot_b magisk_patched_init_boot_b_F29.img
fastboot reboot
```

### 13. Finish Magisk Setup

Open Magisk after boot. If it requests additional setup, allow it and reboot.

### 14. Verify Root

Run:

```bash
adb shell su -c id
```

Successful result:

```text
uid=0(root) gid=0(root) context=u:r:magisk:s0
```

### 15. Clean Up DSU

After root is confirmed:

```bash
adb shell gsi_tool wipe
```

Verify:

```bash
adb shell gsi_tool status
```

Expected:

```text
normal
```

## Troubleshooting Lessons

- If ADB is unauthorized, the fix is on the phone screen, not the PC.
- If the OTA payload uses `BROTLI_BSDIFF`, it is incremental and cannot produce a complete image alone.
- A zero-byte `init_boot.img` must never be flashed.
- The active slot matters. Flash `init_boot_b` only if current slot is `b`.
- Official Google GSIs may boot but still block `adb root`.
- A debuggable/root-capable GSI is needed for the DSU partition-pull method.
- If the phone boots after flashing but `su` is missing, open Magisk and complete additional setup.
- Always keep the stock `init_boot` backup.

## Safety Rules For The AI

- Never relock the bootloader while modified images are flashed.
- Never flash images from a different model, region, slot, or build.
- Never continue if the extracted image is zero bytes.
- Always verify current slot before flashing.
- Always preserve the stock image before flashing patched images.
- Stop and ask before destructive steps like bootloader unlock or relock.
- Prefer reversible actions.
- Do not bypass app security checks or hide root for protected apps.

## Final Outcome

The device was rooted successfully by pulling the exact stock `init_boot` from the phone using temporary DSU root, patching it with Magisk, and flashing it back to the active slot.
