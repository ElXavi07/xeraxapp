# Claude handoff: add Xerax Root to xeraxapp.com

## What you received

- `xerax-root-website-preview.zip`: static files intended for the `/root/` route.
- `xerax-root-source.zip`: companion source, tests, profiles, build scripts, and docs.
- `XeraxRootCompanion-0.3.0-windows-x64.exe`: unsigned preview executable.

The website is a static console. It talks only to the local companion at
`http://127.0.0.1:47721`; the website itself cannot execute ADB or fastboot.

## Integration request

1. Add a `/root/` route to the existing Xerax website.
2. Preserve the supplied `index.html`, `styles.css`, `app.js`, `release.json`,
   `_headers`, and `downloads/` relative paths.
3. Adapt only the shared Xerax header/footer and typography if needed. Do not
   rewrite the local-agent API contract.
4. Serve `release.json` with `Cache-Control: no-store`.
5. Serve versioned executables as immutable downloads.
6. Apply every security header in `_headers`, especially the CSP allowing
   `http://127.0.0.1:47721` in `connect-src`.
7. Do not proxy, log, or upload pairing codes, serial numbers, boot images,
   device properties, or terminal output.
8. Keep the unsigned-preview warning visible until a signed build replaces it.

## Release gate

Do not present this as production-ready or universally compatible yet.

Before public launch:

- Sign the executable with a trusted Xerax Authenticode certificate.
- Run `companion/sign.ps1`, then regenerate the deployment bundle.
- Confirm `release.json` has `"signed": true`.
- Test the complete workflow on physical unlocked devices.
- Add a profile only after detect, image acquisition, Magisk patching, flashing,
  reboot, and `su -c id` verification pass for that exact product/build.

The current profile manifest is empty. Unknown devices receive guarded manual
guidance and must not be advertised as one-click supported.

## Verification checklist

- `/root/` returns HTTP 200.
- The companion download hash matches `release.json`.
- Pairing connects from the production HTTPS origin to localhost.
- Platform Tools status renders for both ADB and fastboot.
- Incremental OTA errors such as `BROTLI_BSDIFF` produce a stop result.
- Zero-byte images are rejected.
- DSU/GSI guidance remains profile-gated and is never run automatically.
- The flash endpoint still requires unlock verification, serial confirmation,
  matching profile/partition, backup confirmation, and Magisk confirmation.

## Files Claude should read first

1. `docs/architecture.md`
2. `docs/troubleshooting.md`
3. `docs/deployment.md`
4. `agent/xerax_agent.py`
5. `profiles/device_profiles.json`

The main rule: improve the presentation freely, but do not weaken the companion’s
fail-closed checks or let an AI generate executable rooting commands.
