# Root troubleshooting knowledge model

The first reviewed training case is a successful OnePlus 12R NA (`CPH2611`)
running build `CPH2611_11.F.29_2290_202604031213`. Its stock `init_boot_b`
partition was read from a temporary debuggable DSU environment, patched by
Magisk, flashed back to the active slot, and verified with `su -c id`.

That case supplies evidence for failure classification, but it does not make its
DSU/GSI procedure universal.

## Portable rules

These observations safely generalize:

- `adb unauthorized` requires approval on the phone.
- `BROTLI_BSDIFF` and similar source-copy operations indicate an incremental OTA.
- Zero-byte extraction output is never flashable.
- Many bootloaders do not implement `fastboot fetch`.
- Normal Android ADB shells generally cannot read `/dev/block/by-name/*`.
- The current A/B slot must be checked before backup and again before flashing.
- Booting successfully is not proof of root; `su -c id` must return `uid=0`.
- Never relock a bootloader while modified partitions are installed.

## Profile-gated rules

The following require exact-device evidence and are never selected or executed by
AI:

- choosing a GSI;
- staging or enabling DSU;
- using `adb root` in a temporary system;
- reading a named block partition;
- deciding whether the device uses `boot`, `init_boot`, or another partition;
- choosing slot-specific flash targets.

Before Xerax automates one of these operations, a device profile needs the exact
product identifier, model/region/build constraints, known partition layout,
tested image checksum/source, rollback process, and physical-device test record.

## AI role

AI may explain a deterministic diagnostic result in simpler language. It may not
invent commands, select firmware, select a GSI, choose a partition, or turn a
single-device success into an executable rule for another model.
